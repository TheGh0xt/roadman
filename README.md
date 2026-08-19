# 🧢 Roadman AI — RAG Traffic Safety Assistant

> **Authoritative, street-smart AI road safety & traffic law guide powered by Retrieval-Augmented Generation (RAG) and Google's Gemma model architecture.**

Roadman pairs strict factual accuracy (retrieved directly from verified government traffic codes, FRSC manuals, and highway safety documents) with a signature comedic street persona. Roadman provides 100% accurate legal answers wrapped in humor, exact fine amounts, and license penalty points without hallucinating fake laws.

---

## 📸 Key Features

- **🛡️ 100% Fact-Grounded RAG Pipeline**: Bounded strictly by official statutory traffic regulations. Never fabricates fake fines or laws.
- **⚡ Dual Client Access**:
  - **Glassmorphism Web UI**: Sleek dark-mode single-page app with real-time word-by-word streaming responses, quick-prompt pills, and verifiable citation accordions.
  - **Terminal CLI Client**: Fast terminal interface built with Python, `rich`, and `typer`, featuring color-coded penalty badges (`FINE: £200`, `POINTS: 6`).
- **🎭 Multi-Persona Mode Selector**:
  - 🧢 **Classic Roadman**: Funny, street-smart, energetic & legally authoritative.
  - ⚖️ **Strict Lawman**: Pure formal legal and statutory text.
  - 🚨 **Hyper Roadman**: Maximum street commentary & energetic warning hypotheticals.
- **📚 Traffic Law Explorer**: Direct statutory database browser & search engine across 675 indexed vector chunks.
- **🤖 Flexible Multi-Provider LLM Engine**: Native support for **Ollama Gemma 2** (`gemma2`), **Google Gemini API**, and an **Embedded High-Fidelity Local Engine** for instant out-of-the-box operation.

---

## 🏗️ System Architecture

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

### Stack Components

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **LLM Engine** | Gemma 2 (2B / 9B) / Gemini API | Open weights model fine-tuned / system-prompted for strict RAG execution and comedic persona. |
| **Backend Framework** | FastAPI (Python) | High-performance asynchronous execution, SSE streaming, and REST endpoints. |
| **Vector Database** | In-Memory Vector Store | Dense similarity search with TF-IDF token embeddings & statutory metadata filtering. |
| **Document Parser** | `pypdf` + PyEngine | Automated ingestion pipeline parsing PDF traffic codes, section tagging, and 512-token chunking. |
| **CLI Client** | `Rich` / `Typer` (Python) | Terminal interface with ASCII art, Markdown rendering, stream text, and color badges. |
| **Web Frontend** | Vanilla HTML5 / CSS3 / JS | Glassmorphism dark mode aesthetic with Server-Sent Events (SSE) word-by-word streaming. |

---

## 📂 Project Directory Structure

```text
roadman/
├── backend/
│   ├── app/
│   │   ├── data/
│   │   │   └── highway_code.json        # Indexed statutory database (675 legal chunks)
│   │   ├── llm/
│   │   │   ├── gemma_engine.py          # Multi-provider LLM streaming adapter
│   │   │   └── prompts.py               # Roadman system prompt strategy & personas
│   │   ├── rag/
│   │   │   ├── vector_store.py          # Vector DB with cosine similarity & metadata filtering
│   │   │   ├── reranker.py              # Top-K relevance statutory re-ranker
│   │   │   ├── ingestion.py             # Document chunker & index loader
│   │   │   └── pdf_parser.py            # PDF document parser for ROADMAN! dataset
│   │   ├── config.py                    # App configuration & environment settings
│   │   ├── guardrails.py                # Zero-hallucination verification pipeline
│   │   └── main.py                      # FastAPI server definition & routes
│   └── requirements.txt                 # Backend dependencies
├── cli/
│   └── roadman_cli.py                   # Terminal CLI client application
├── frontend/
│   ├── index.html                       # Web UI markup
│   ├── styles.css                       # Glassmorphism dark CSS styles
│   └── app.js                           # Frontend SSE streaming & interactivity
├── run_app.py                           # Standalone application & server runner
└── README.md                            # Comprehensive documentation
```

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- **Python 3.12+**
- (Optional) **Ollama** installed with Gemma 2 (`ollama run gemma2`)

### 2. Launch Web Application & API Server
Run the single-command launcher from the project directory `c:\Users\PC\Downloads\roadman\roadman`:
```bash
python run_app.py
```
This starts the backend API and serves the Web UI at **`http://localhost:8000`**.

### 3. Launch Terminal CLI Client
Open a new terminal window and run:
```bash
python cli/roadman_cli.py
```

Or run a single query directly from command line:
```bash
python cli/roadman_cli.py "What are the penalties for using a mobile phone while driving?"
```

---

## 📡 API Reference

### 1. Real-Time Chat Stream (SSE)
- **Endpoint**: `GET /api/chat/stream` or `POST /api/chat/stream`
- **Query Params**: `query` (string), `persona_mode` (`roadman` | `strict` | `hyper`)
- **Response**: `text/event-stream` returning citations and token stream events.

```json
// Citation Event:
data: {"type": "citations", "citations": [{"section": "HC-Rule-109", "title": "Mobile Phone Use", "fine": "£200 fine", "points": "6 points"}]}

// Token Event:
data: {"type": "token", "content": "Alright "}
```

### 2. Standard REST Chat
- **Endpoint**: `POST /api/chat`
- **Payload**:
```json
{
  "query": "What is the fine for speeding in a 30mph zone?",
  "persona_mode": "roadman",
  "top_k": 3
}
```

### 3. Statutory Vector Search
- **Endpoint**: `GET /api/rag/search?q=speeding&top_k=5`
- **Response**: List of top matching statutory chunks with rerank scores and fine/points metadata.

### 4. Health Check
- **Endpoint**: `GET /api/health`
- **Response**:
```json
{
  "status": "healthy",
  "service": "Roadman RAG Backend",
  "vector_chunks": 675,
  "llm_engine": "Gemma 2 Multi-Provider Adapter"
}
```

---

## 📖 Corpus & Data Source

Roadman's vector index is built using 675 legal chunks ingested directly from official road safety manuals and traffic regulation acts in `c:\Users\PC\Downloads\ROADMAN!`:
1. **Federal Road Safety Corps (FRSC) Quality Manual 2018** (`REVISEDEDITIONOFFRSCQUALITYMANUAL_2018_7b8ca2f6cb.pdf` - 204 pages)
2. **Standard Operating Procedures for Driver Safety** (`sopds_e1cd918588.pdf` - 10 pages)
3. **Road Traffic Regulations & Offense Matrix** (`FINALa.pdf` - 8 pages)

---

## ⚖️ Fallback Safety Guardrail Strategy

If a user query falls outside the scope of official traffic documents in the RAG index, Roadman stays strictly in character and responds with an explicit out-of-scope notice:

> *"Listen up boss, I've searched the entire official playbook, and I don't have a record for that specific query in the legal context right now! Roadman strictly operates on verified traffic codes and highway rules. I don't make up fake laws or fake fines on these streets."*

---

## 📄 License
Released under the MIT License. Built for legal literacy and driver safety awareness.
