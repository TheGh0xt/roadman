import os
import sys
import http.server
import socketserver
import urllib.parse
import json
import asyncio
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.rag.vector_store import vector_store
from app.rag.ingestion import load_and_index_corpus
from app.rag.reranker import Reranker
from app.llm.gemma_engine import llm_engine

PORT = 8000
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

class RoadmanRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/health":
            self.send_json_response({
                "status": "healthy",
                "service": "Roadman RAG Backend",
                "vector_chunks": len(vector_store.documents),
                "llm_engine": "Gemma 2 Multi-Provider Adapter"
            })
            return

        elif path == "/api/rag/search":
            q = query_params.get("q", [""])[0]
            top_k = int(query_params.get("top_k", ["3"])[0])
            candidates = vector_store.search(q, top_k=top_k * 2)
            reranked = Reranker.rerank(q, candidates, top_k=top_k)
            self.send_json_response({
                "query": q,
                "results_count": len(reranked),
                "chunks": reranked
            })
            return

        elif path == "/api/chat/stream":
            q = query_params.get("query", [""])[0]
            persona = query_params.get("persona_mode", ["roadman"])[0]
            self.handle_sse_stream(q, persona)
            return

        # Serve static frontend files
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ["/api/chat", "/api/chat/stream"]:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = json.loads(body)
            except Exception:
                data = {}
            q = data.get("query", "")
            persona = data.get("persona_mode", "roadman")

            if parsed.path == "/api/chat/stream":
                self.handle_sse_stream(q, persona)
            else:
                self.handle_rest_chat(q, persona)
            return

    def send_json_response(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_rest_chat(self, query: str, persona: str):
        candidates = vector_store.search(query, top_k=6)
        retrieved_chunks = Reranker.rerank(query, candidates, top_k=3)

        async def collect():
            tokens = []
            async for token in llm_engine.generate_stream(query, retrieved_chunks, persona):
                tokens.append(token)
            return "".join(tokens)

        answer = asyncio.run(collect())
        citations = [
            {
                "section": c["metadata"].get("section_number"),
                "title": c["metadata"].get("title"),
                "fine": c["metadata"].get("fine"),
                "points": c["metadata"].get("points")
            }
            for c in retrieved_chunks
        ]
        self.send_json_response({
            "query": query,
            "persona_mode": persona,
            "answer": answer,
            "citations": citations
        })

    def handle_sse_stream(self, query: str, persona: str):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        candidates = vector_store.search(query, top_k=6)
        retrieved_chunks = Reranker.rerank(query, candidates, top_k=3)

        citations_event = {
            "type": "citations",
            "citations": [
                {
                    "section": c["metadata"].get("section_number"),
                    "title": c["metadata"].get("title"),
                    "fine": c["metadata"].get("fine"),
                    "points": c["metadata"].get("points")
                }
                for c in retrieved_chunks
            ]
        }
        self.wfile.write(f"data: {json.dumps(citations_event)}\n\n".encode('utf-8'))
        self.wfile.flush()

        async def stream():
            async for token in llm_engine.generate_stream(query, retrieved_chunks, persona):
                token_event = {"type": "token", "content": token}
                self.wfile.write(f"data: {json.dumps(token_event)}\n\n".encode('utf-8'))
                self.wfile.flush()

        asyncio.run(stream())

        done_event = {"type": "done"}
        self.wfile.write(f"data: {json.dumps(done_event)}\n\n".encode('utf-8'))
        self.wfile.flush()

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("[+] Initializing Roadman RAG Index...")
    count = load_and_index_corpus()
    print(f"[+] Loaded {count} legal chunks into Vector Database.")

    print(f"\n[+] Roadman Web Application & API Server running at http://localhost:{PORT}")
    print(f"[+] Roadman CLI Client ready! Run 'python cli/roadman_cli.py'")

    with socketserver.TCPServer(("", PORT), RoadmanRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Roadman server.")

if __name__ == "__main__":
    main()
