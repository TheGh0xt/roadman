import json
import asyncio
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.rag.vector_store import vector_store
from app.rag.ingestion import load_and_index_corpus
from app.rag.reranker import Reranker
from app.llm.gemma_engine import llm_engine
from app.guardrails import guardrails

app = FastAPI(
    title="Roadman AI - RAG Traffic Safety Assistant",
    version="1.0.0",
    description="Authoritative, street-smart AI road safety RAG engine powered by Gemma 2 & FastAPI"
)

# Enable CORS for web frontend & CLI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    persona_mode: Optional[str] = "roadman"  # "roadman", "strict", "hyper"
    top_k: Optional[int] = 3

@app.on_event("startup")
async def startup_event():
    """Load legal corpus into vector store on startup."""
    total_indexed = load_and_index_corpus()
    print(f"✅ Roadman RAG Database Initialized: {total_indexed} chunks indexed into vector store.")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Roadman RAG Backend",
        "vector_chunks": len(vector_store.documents),
        "llm_engine": "Gemma 2 / Multi-Provider Engine"
    }

@app.get("/api/rag/search")
async def search_rag(q: str = Query(..., description="Legal or traffic question"), top_k: int = 3):
    """Expose RAG vector search directly for legal clause verification."""
    candidates = vector_store.search(q, top_k=top_k * 2)
    reranked = Reranker.rerank(q, candidates, top_k=top_k)
    return {
        "query": q,
        "results_count": len(reranked),
        "chunks": reranked
    }

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    Standard JSON Chat Endpoint with full response and source citations.
    """
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve RAG chunks
    candidates = vector_store.search(payload.query, top_k=(payload.top_k or 3) * 2)
    retrieved_chunks = Reranker.rerank(payload.query, candidates, top_k=payload.top_k or 3)

    # 2. Generate response text
    response_tokens = []
    async for token in llm_engine.generate_stream(payload.query, retrieved_chunks, payload.persona_mode):
        response_tokens.append(token)

    full_answer = "".join(response_tokens)

    # 3. Guardrail check
    guardrail_report = guardrails.verify_grounding(full_answer, retrieved_chunks)

    # 4. Extract citations
    citations = [
        {
            "section": c["metadata"].get("section_number"),
            "title": c["metadata"].get("title"),
            "fine": c["metadata"].get("fine"),
            "points": c["metadata"].get("points"),
            "source": c["metadata"].get("source")
        }
        for c in retrieved_chunks
    ]

    return {
        "query": payload.query,
        "persona_mode": payload.persona_mode,
        "answer": full_answer,
        "citations": citations,
        "guardrail": guardrail_report
    }

@app.post("/api/chat/stream")
@app.get("/api/chat/stream")
async def chat_stream_endpoint(query: str = Query(None), persona_mode: str = Query("roadman"), request: Request = None):
    """
    Server-Sent Events (SSE) Real-Time Word-by-Word Streaming Endpoint.
    Accepts query via GET query param or POST JSON body.
    """
    user_query = query
    if not user_query and request and request.method == "POST":
        try:
            body = await request.json()
            user_query = body.get("query")
            persona_mode = body.get("persona_mode", persona_mode)
        except Exception:
            pass

    if not user_query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")

    candidates = vector_store.search(user_query, top_k=6)
    retrieved_chunks = Reranker.rerank(user_query, candidates, top_k=3)

    async def sse_generator():
        # First send RAG metadata event
        meta_event = {
            "type": "citations",
            "citations": [
                {
                    "section": c["metadata"].get("section_number"),
                    "title": c["metadata"].get("title"),
                    "fine": c["metadata"].get("fine"),
                    "points": c["metadata"].get("points"),
                    "source": c["metadata"].get("source")
                }
                for c in retrieved_chunks
            ]
        }
        yield f"data: {json.dumps(meta_event)}\n\n"

        # Stream LLM tokens
        async for token in llm_engine.generate_stream(user_query, retrieved_chunks, persona_mode):
            token_event = {"type": "token", "content": token}
            yield f"data: {json.dumps(token_event)}\n\n"

        # Send completion event
        end_event = {"type": "done"}
        yield f"data: {json.dumps(end_event)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# Host Web UI static files
import os
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
