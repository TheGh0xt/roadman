import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CORPUS_FILE = DATA_DIR / "highway_code.json"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K = 3
RERANK_TOP_K = 3
