import sys
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    from rich.theme import Theme
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Backend URL config
SERVER_URL = "http://127.0.0.1:8000"

def get_console():
    if RICH_AVAILABLE:
        custom_theme = Theme({
            "roadman.title": "bold yellow on black",
            "roadman.badge": "bold black on yellow",
            "legal.section": "bold cyan",
            "fine.badge": "bold white on red",
            "points.badge": "bold black on bright_yellow",
            "success": "green",
            "warning": "yellow",
            "danger": "red"
        })
        return Console(theme=custom_theme)
    return None

console = get_console()

ASCII_HEADER = r"""
 [bold yellow] ____   ___   _     ____  __  __    _    _   _ [/bold yellow]
 [bold yellow]|  _ \ / _ \ / \   |  _ \|  \/  |  / \  | \ | |[/bold yellow]
 [bold yellow]| |_) | | | / _ \  | | | | |\/| | / _ \ |  \| |[/bold yellow]
 [bold yellow]|  _ <| |_| / ___ \ | |_| | |  | |/ ___ \| |\  |[/bold yellow]
 [bold yellow]|_| \_\\___/_/   \_\|____/|_|  |_/_/   \_\_| \_|[/bold yellow]
 [bold cyan]  -- Official AI RAG Traffic Safety Assistant --  [/bold cyan]
"""

def print_header():
    if console:
        console.print(ASCII_HEADER)
        console.print(Panel(
            "[bold white]Roadman[/bold white] is live! Ask any question about speed limits, mobile phones, red lights, fines & license points.",
            title="[bold yellow] STREET LEGAL GUIDE [/bold yellow]",
            subtitle="[dim]Powered by Gemma 2 & RAG Engine[/dim]",
            border_style="yellow"
        ))
    else:
        print("==================================================")
        print(" ROADMAN - AI RAG Traffic Safety Assistant ")
        print("==================================================")

def query_backend_standalone(query: str, persona_mode: str = "roadman"):
    """Fall back to direct Python backend execution if local FastAPI server isn't active."""
    from app.rag.vector_store import vector_store
    from app.rag.ingestion import load_and_index_corpus
    from app.rag.reranker import Reranker
    from app.llm.gemma_engine import llm_engine

    if len(vector_store.documents) == 0:
        load_and_index_corpus()

    candidates = vector_store.search(query, top_k=6)
    retrieved_chunks = Reranker.rerank(query, candidates, top_k=3)

    citations = [
        {
            "section": c["metadata"].get("section_number"),
            "title": c["metadata"].get("title"),
            "fine": c["metadata"].get("fine"),
            "points": c["metadata"].get("points")
        }
        for c in retrieved_chunks
    ]

    return llm_engine.generate_stream(query, retrieved_chunks, persona_mode), citations

def stream_query(query: str, persona_mode: str = "roadman"):
    if console:
        console.print(f"\n[bold yellow]🗣 You asked:[/bold yellow] [italic]{query}[/italic]\n")

    # Try streaming from FastAPI server first
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"{SERVER_URL}/api/chat/stream?query={encoded_q}&persona_mode={persona_mode}"
        req = urllib.request.Request(url)
        res = urllib.request.urlopen(req, timeout=3)
        
        full_text = ""
        citations = []
        
        if console:
            console.print("[bold cyan]🤖 Roadman is retrieving official traffic codes...[/bold cyan]\n")
        
        for line in res:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                event_data = json.loads(line_str[6:])
                if event_data.get("type") == "citations":
                    citations = event_data.get("citations", [])
                    if console and citations:
                        console.print(f"[bold cyan]🔍 RAG Matched Section:[/bold cyan] [bold yellow]{citations[0]['section']}[/bold yellow] - {citations[0]['title']}")
                        if citations[0].get('fine'):
                            console.print(f"[bold white on red] FINE: {citations[0]['fine']} [/bold white on red]  [bold black on yellow] POINTS: {citations[0]['points']} [/bold black on yellow]\n")
                elif event_data.get("type") == "token":
                    token = event_data.get("content", "")
                    full_text += token
                    if console:
                        console.print(token, end="", flush=True)
                    else:
                        sys.stdout.write(token)
                        sys.stdout.flush()
        
        if console:
            console.print("\n")
        return

    except Exception:
        # Server not running -> run via direct embedded RAG engine
        stream_gen, citations = query_backend_standalone(query, persona_mode)
        if console and citations:
            console.print(f"[bold cyan]🔍 RAG Matched Section:[/bold cyan] [bold yellow]{citations[0]['section']}[/bold yellow] - {citations[0]['title']}")
            if citations[0].get('fine'):
                console.print(f"[bold white on red] FINE: {citations[0]['fine']} [/bold white on red]  [bold black on yellow] POINTS: {citations[0]['points']} [/bold black on yellow]\n")
        
        full_text = ""
        import asyncio
        
        async def run_async_stream():
            async for token in stream_gen:
                if console:
                    console.print(token, end="", flush=True)
                else:
                    sys.stdout.write(token)
                    sys.stdout.flush()
        
        asyncio.run(run_async_stream())
        if console:
            console.print("\n")

def interactive_loop():
    print_header()
    persona_mode = "roadman"
    
    if console:
        console.print("[dim]Type your question, '/persona' to switch mode, or 'exit' / 'q' to quit.[/dim]\n")
    
    while True:
        try:
            if console:
                query = console.input("[bold yellow]Roadman-CLI>[/bold yellow] ").strip()
            else:
                query = input("Roadman-CLI> ").strip()

            if not query:
                continue

            if query.lower() in ["exit", "quit", "q"]:
                if console:
                    console.print("[bold yellow]Stay safe on the roads my g! Peace out. 🚗💨[/bold yellow]")
                break

            if query.lower() == "/persona":
                if console:
                    console.print("Select persona mode: [1] Roadman (Classic) [2] Strict Lawman [3] Hyper-Roadman")
                    choice = console.input("Choice (1-3): ").strip()
                    if choice == "2":
                        persona_mode = "strict"
                        console.print("[bold green]Mode set to Strict Lawman ⚖️[/bold green]")
                    elif choice == "3":
                        persona_mode = "hyper"
                        console.print("[bold yellow]Mode set to Hyper Roadman 🚨[/bold yellow]")
                    else:
                        persona_mode = "roadman"
                        console.print("[bold yellow]Mode set to Classic Roadman 🧢[/bold yellow]")
                continue

            stream_query(query, persona_mode)

        except KeyboardInterrupt:
            print("\nExiting Roadman CLI...")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        single_query = " ".join(sys.argv[1:])
        stream_query(single_query)
    else:
        interactive_loop()
