import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Candidate source folders containing the user's PDF documents
CANDIDATE_DATA_DIRS = [
    Path(__file__).resolve().parent.parent.parent,  # Current repo root
    Path(r"c:\Users\PC\Downloads\ROADMAN!"),
    Path(r"c:\Users\PC\Desktop\Coding\roadman\roadman")
]
CORPUS_OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "highway_code.json"

def parse_pdf_documents() -> List[Dict[str, Any]]:
    """
    Parses PDF documents from candidate directories and converts them into
    structured legal and road safety rules for RAG vector index.
    """
    extracted_laws = []
    pdf_files = []
    seen_files = set()

    for candidate_dir in CANDIDATE_DATA_DIRS:
        if candidate_dir.exists():
            for f in list(candidate_dir.glob("*.pdf")) + list(candidate_dir.glob("*.PDF")):
                if f.name not in seen_files:
                    seen_files.add(f.name)
                    pdf_files.append(f)

    print(f"[+] Found {len(pdf_files)} PDF documents across project directories: {[f.name for f in pdf_files]}")

    try:
        import pypdf
        use_pypdf = True
    except ImportError:
        use_pypdf = False
        print("[!] pypdf not available, using built-in regex text extraction.")

    law_id = 100

    for pdf_file in pdf_files:
        doc_name = pdf_file.name
        full_text = ""

        if use_pypdf:
            try:
                reader = pypdf.PdfReader(str(pdf_file))
                print(f"[+] Reading {doc_name} ({len(reader.pages)} pages)...")
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    full_text += f"\n--- Page {page_num + 1} ---\n" + text
            except Exception as e:
                print(f"Error reading {doc_name} with pypdf: {e}")
        else:
            with open(pdf_file, "rb") as f:
                content = f.read().decode("latin1", errors="ignore")
                full_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)

        # Normalize multiple blank lines and clean text
        cleaned_full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        paragraphs = [p.strip() for p in cleaned_full_text.split("\n\n") if len(re.sub(r'\s+', '', p)) > 60]

        # Extract penalty codes, fines, points, and statutory regulations
        for idx, para in enumerate(paragraphs):
            # Clean up page marker lines
            clean_para = re.sub(r'--- Page \d+ ---', '', para).strip()
            lines = [l.strip() for l in clean_para.split("\n") if l.strip()]
            title = lines[0][:80].strip() if lines else f"Rule from {doc_name}"
            
            fine_match = re.search(r'(?:fine|penalty|naira|₦|\$|£|cost)\s*[:=]?\s*([^\n.,;]+)', clean_para, re.IGNORECASE)
            points_match = re.search(r'(\d+)\s*(?:points|penalty points)', clean_para, re.IGNORECASE)
            sec_match = re.search(r'(?:section|rule|code|article|chapter)\s*(\d+[A-Za-z0-9\-\.]*)', clean_para, re.IGNORECASE)

            fine_val = fine_match.group(0).strip() if fine_match else "Standard FRSC/Traffic Fixed Penalty"
            points_val = f"{points_match.group(1)} penalty points" if points_match else "Points according to FRSC Code"
            sec_val = f"FRSC-Sec-{sec_match.group(1)}" if sec_match else f"FRSC-{doc_name[:6]}-Rule-{idx+1}"

            extracted_laws.append({
                "section_number": sec_val,
                "title": title,
                "category": "Federal Road Safety & Traffic Code",
                "jurisdiction": "FRSC / Road Traffic Regulations",
                "fine": fine_val,
                "points": points_val,
                "full_text": clean_para,
                "source_document": doc_name
            })
            law_id += 1

    print(f"[+] Successfully extracted {len(extracted_laws)} legal rules from PDF documents.")
    return extracted_laws

def update_corpus_from_roadman_dir():
    """
    Parses ROADMAN! folder PDFs and merges them with default highway laws into highway_code.json
    """
    parsed_laws = parse_pdf_documents()
    if not parsed_laws:
        return

    # Load existing laws if any
    existing_laws = []
    if CORPUS_OUTPUT_FILE.exists():
        try:
            with open(CORPUS_OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_laws = json.load(f)
        except Exception:
            existing_laws = []

    # Merge avoiding duplicate section numbers
    existing_sections = {law.get("section_number") for law in existing_laws}
    merged_laws = list(existing_laws)

    for law in parsed_laws:
        if law.get("section_number") not in existing_sections:
            merged_laws.append(law)
            existing_sections.add(law.get("section_number"))

    CORPUS_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_laws, f, indent=2)

    print(f"💾 Updated {CORPUS_OUTPUT_FILE} with total {len(merged_laws)} legal records!")
