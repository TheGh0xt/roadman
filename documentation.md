# 📚 Technical Documentation — Roadman AI RAG Assistant

**Roadman** is an AI-powered retrieval-augmented generation (RAG) assistant for traffic safety, road laws, and driver legal requirements accessible via **Terminal CLI** and a **Glassmorphism Web UI**.

---

## 🎯 Executive Summary & Objectives

- **Primary Goal**: Deliver 100% legally accurate, verifiable answers to road safety & traffic regulation questions using official statutory documentation bounded by a zero-hallucination RAG pipeline.
- **Delivery Vehicle**: Answers are wrapped in Roadman's signature comedic street-smart persona, breaking down complex legal jargon into entertaining, memorable explanations without obscuring statutory fines or penalty points.
- **Interfaces**:
  1. **Web UI**: Modern single-page glassmorphism app with real-time SSE token streaming, persona switching, citation drawers, and an interactive Traffic Law Explorer.
  2. **Terminal CLI Client**: Terminal application built with `rich` and `typer` featuring ASCII art headers, Markdown stream rendering, and color-coded status badges.

---

## 🏗️ System Architecture & Data Flow

```
                                  ┌───────────────────────────┐
                                  │   Clients (CLI / Web UI)   │
                                  └─────────────┬─────────────┘
                                                │ REST / SSE Stream
                                  ┌─────────────▼─────────────┐
                                  │      FastAPI Backend      │
                                  │  ┌─────────────────────┐  │
                                  │  │ Guardrails & Logic  │  │
                                  │  └──────────┬──────────┘  │
                                  └─────────────┼─────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │        RAG Pipeline       │
                                  │  ┌─────────────────────┐  │
                                  │  │ Vector Store +      │  │
                                  │  │ Gemma / LLM Engine  │  │
                                  │  └─────────────────────┘  │
                                  └───────────────────────────┘
```

### Data Pipeline & RAG Workflow

1. **Document Ingestion (`backend/app/rag/pdf_parser.py` & `ingestion.py`)**:
   - Parses PDF documents from project directory & `c:\Users\PC\Downloads\ROADMAN!`:
     - `REVISEDEDITIONOFFRSCQUALITYMANUAL_2018_7b8ca2f6cb.pdf` (204 pages)
     - `sopds_e1cd918588.pdf` (10 pages)
     - `FINALa.pdf` (8 pages)
   - Splits text into 512-token chunks with 64-token overlap.
   - Tags each chunk with statutory metadata: `section_number`, `title`, `fine`, `points`, `category`, `jurisdiction`, `source_document`.

2. **Vector Indexing & Search (`backend/app/rag/vector_store.py`)**:
   - Computes TF-IDF & dense token similarity weights.
   - Calculates cosine distance and statutory keyword boost factors.

3. **Re-Ranking (`backend/app/rag/reranker.py`)**:
   - Scores candidate chunks against query terms, fine queries, and penalty point flags to select the Top-3 most relevant statutory clauses.

4. **Multi-Provider Generation (`backend/app/llm/gemma_engine.py`)**:
   - Streams responses word-by-word via Server-Sent Events (SSE).
   - Adapts dynamically to local **Ollama Gemma 2** (`gemma2`), **Google Gemini API**, or an **Embedded High-Fidelity Local Persona Engine**.

---

## 🛠️ API Documentation

### 1. Server-Sent Events (SSE) Chat Stream
- **URL**: `/api/chat/stream`
- **Method**: `GET` / `POST`
- **Parameters**:
  - `query` (string, required): Legal query (e.g. "What is the penalty for using a phone while driving?")
  - `persona_mode` (string, optional): `roadman` (default) | `strict` | `hyper`

#### Stream Events
```json
// Citation Event
data: {
  "type": "citations",
  "citations": [
    {
      "section": "HC-Rule-109",
      "title": "Using a Hand-Held Mobile Phone While Driving",
      "fine": "£200 fine and 6 penalty points",
      "points": "6 points"
    }
  ]
}

// Token Stream Event
data: { "type": "token", "content": "Alright " }

// Completion Event
data: { "type": "done" }
```

### 2. Standard REST Chat Endpoint
- **URL**: `/api/chat`
- **Method**: `POST`
- **Request Body**:
```json
{
  "query": "What is the fine for speeding in a 30 zone?",
  "persona_mode": "roadman",
  "top_k": 3
}
```
- **Response**:
```json
{
  "query": "What is the fine for speeding in a 30 zone?",
  "persona_mode": "roadman",
  "answer": "Alright boss, check the vibe on Speeding...",
  "citations": [ ... ],
  "guardrail": {
    "grounded": true,
    "confidence_score": 0.98,
    "status": "PASS_ZERO_HALLUCINATION"
  }
}
```

### 3. Statutory Vector Search Endpoint
- **URL**: `/api/rag/search`
- **Method**: `GET`
- **Parameters**: `q` (search query), `top_k` (default 3)

---

## 💻 Terminal CLI Documentation

### Command Execution
```bash
# 1. Interactive Chat Loop
python cli/roadman_cli.py

# 2. Direct Single Query
python cli/roadman_cli.py "What are the FRSC rules for seatbelt compliance?"
```

### CLI Features
- **ASCII Art Header**: Street-style branding banner.
- **RAG Badges**: Highlighted statutory section number, fine badge (`[FINE: £200]`), and penalty points badge (`[POINTS: 6]`).
- **Interactive Persona Toggle**: Type `/persona` during interactive mode to switch between Classic Roadman, Strict Lawman, and Hyper Roadman.

---

## 🌐 Web UI Features & Layout

- **Glassmorphism Dark Theme**: Midnight blue background (`#090d16`) with glowing yellow (`#facc15`) and cyan (`#06b6d4`) accents.
- **Live Stream Box**: Word-by-word streaming canvas using SSE with markdown formatting.
- **Quick-Prompt Pills**: Clickable chips for popular queries (Mobile phone fines, FRSC speeding rules, DUI alcohol limits, Zebra crossings, seatbelts, uninsured driving).
- **Traffic Law Explorer Tab**: Browsable grid displaying all 675 indexed statutory rules with live search filtering.

---

## 🚀 Execution Commands

| Task | Command |
| :--- | :--- |
| **Launch Server & Web App** | `python run_app.py` |
| **Run CLI Client** | `python cli/roadman_cli.py` |
| **Re-index PDFs** | `python -c "import sys; sys.path.insert(0, 'backend'); from app.rag.pdf_parser import update_corpus_from_roadman_dir; update_corpus_from_roadman_dir()"` |
