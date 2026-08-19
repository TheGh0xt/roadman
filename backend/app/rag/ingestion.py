import json
import os
from pathlib import Path
from typing import List, Dict, Any
from app.config import CORPUS_FILE, CHUNK_SIZE, CHUNK_OVERLAP
from app.rag.vector_store import vector_store

def recursive_character_chunker(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into chunks of specified size with overlap.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def load_and_index_corpus() -> int:
    """
    Load traffic laws database and populate vector store.
    """
    if not os.path.exists(CORPUS_FILE):
        try:
            from app.rag.pdf_parser import update_corpus_from_roadman_dir
            update_corpus_from_roadman_dir()
        except Exception as e:
            print(f"Note: PDF parser info: {e}")
            seed_default_corpus()

    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        laws_data = json.load(f)

    docs_to_index = []
    doc_id = 1

    for law in laws_data:
        rule_text = f"Section {law.get('section_number')}: {law.get('title')}. {law.get('full_text')} " \
                    f"Fine: {law.get('fine')}. Points: {law.get('points')}. Category: {law.get('category')}."

        chunks = recursive_character_chunker(rule_text, CHUNK_SIZE, CHUNK_OVERLAP)

        for idx, chunk in enumerate(chunks):
            docs_to_index.append({
                "id": doc_id,
                "text": chunk,
                "metadata": {
                    "section_number": law.get("section_number"),
                    "title": law.get("title"),
                    "fine": law.get("fine"),
                    "points": law.get("points"),
                    "category": law.get("category"),
                    "jurisdiction": law.get("jurisdiction", "General Traffic Law"),
                    "source": "Official Highway & Traffic Regulations Code",
                    "chunk_id": idx + 1
                }
            })
            doc_id += 1

    vector_store.add_documents(docs_to_index)
    return len(docs_to_index)

def seed_default_corpus():
    """
    Seed initial road safety laws corpus covering key traffic regulations.
    """
    Path(CORPUS_FILE).parent.mkdir(parents=True, exist_ok=True)
    default_laws = [
        {
            "section_number": "HC-Rule-109",
            "title": "Using a Hand-Held Mobile Phone While Driving",
            "category": "Distracted Driving",
            "jurisdiction": "National Traffic Code",
            "fine": "£200 fine and 6 penalty points on driving licence (can lead to license revocation for new drivers within 2 years)",
            "points": "6 points",
            "full_text": "It is illegal to hold and use a phone, sat nav, tablet, or any device that can send or receive data while driving or riding a motorcycle. This includes holding your phone to check notifications, take photos, or scroll playlists while stopped at traffic lights or queuing in traffic. You can get 6 penalty points and a £200 fine. If you passed your driving test within the last 2 years, your license will be revoked automatically."
        },
        {
            "section_number": "HC-Rule-175",
            "title": "Red Light and Traffic Signal Violations",
            "category": "Traffic Signals",
            "jurisdiction": "National Traffic Code",
            "fine": "£100 fine and 3 penalty points",
            "points": "3 points",
            "full_text": "You MUST stop behind the white stop line at traffic lights unless the signal is green. Amber means STOP unless you have crossed the stop line or are so close that stopping might cause a collision. Disobeying red or amber lights incurs a standard £100 fine and 3 penalty points. Failure to stop at a red light captured by safety cameras will result in a fixed penalty notice."
        },
        {
            "section_number": "HC-Rule-124",
            "title": "Exceeding Speed Limits in Built-Up and Residential Areas",
            "category": "Speeding",
            "jurisdiction": "National Traffic Code",
            "fine": "From £100 up to £1,000 max (£2,500 on motorways), 3 to 6 penalty points or driving ban",
            "points": "3 to 6 points or disqualification",
            "full_text": "You MUST NOT exceed the maximum speed limit specified for the road and for your vehicle. Street lights usually mean a 30 mph (48 km/h) speed limit applies unless signs indicate otherwise. Band A speeding (e.g. 31-40mph in 30 zone) results in 3 points and 50% weekly income fine. Band B/C speeding results in 4-6 points or up to 56 days driving ban."
        },
        {
            "section_number": "HC-Rule-95",
            "title": "Driving Under the Influence of Alcohol or Drugs (DUI / DWI)",
            "category": "Impaired Driving",
            "jurisdiction": "National Traffic Code",
            "fine": "Unlimited fine, minimum 12-month driving ban, up to 6 months imprisonment",
            "points": "Automatic driving ban / disqualification",
            "full_text": "Strict legal blood alcohol limit is 35 micrograms of alcohol per 100 millilitres of breath (or 80 milligrams per 100ml blood). Driving or attempting to drive while above the legal limit carries penalties including up to 6 months imprisonment, an unlimited fine, and a mandatory minimum 12-month driving ban (3 years if convicted twice in 10 years)."
        },
        {
            "section_number": "HC-Rule-232",
            "title": "Seat Belt Requirements and Passenger Safety",
            "category": "Vehicle Safety",
            "jurisdiction": "National Traffic Code",
            "fine": "Up to £500 fine",
            "points": "0 points (fixed penalty fine)",
            "full_text": "You MUST wear a seat belt in cars, vans, and other goods vehicles where one is fitted. Drivers are legally responsible for ensuring any child under 14 years old wears a seat belt or uses an approved child restraint. You can be fined up to £500 if you or a child under 14 is not wearing a seatbelt."
        },
        {
            "section_number": "HC-Rule-170",
            "title": "Pedestrian Rights at Zebra and Parallel Crossings",
            "category": "Pedestrian Safety",
            "jurisdiction": "National Traffic Code",
            "fine": "£100 fine and 3 penalty points for careless driving / failing to give way",
            "points": "3 points",
            "full_text": "Drivers MUST yield the right of way and stop when a pedestrian has moved onto a Zebra crossing or is waiting to cross at a junction into which you are turning. Failing to yield to pedestrians waiting at a crossing can incur 3 penalty points and a £100 fine for driving without due care and attention."
        },
        {
            "section_number": "HC-Rule-239",
            "title": "Illegal Parking on Double Yellow Lines and Clearways",
            "category": "Parking & Stopping",
            "jurisdiction": "National Traffic Code",
            "fine": "£70 to £130 Penalty Charge Notice (PCN) + vehicle impoundment fees",
            "points": "0 points (civil enforcement notice)",
            "full_text": "Double yellow lines mean NO PARKING at any time, even for loading or dropping off passengers unless seasonal signs state otherwise. Parking on clearways, cycle lanes, or double yellow lines blocks traffic flow and yields a Penalty Charge Notice up to £130, plus potential towing and impoundment charges."
        },
        {
            "section_number": "HC-Rule-89",
            "title": "Vehicle Insurance Requirements (Driving Without Insurance)",
            "category": "Legal Requirements",
            "jurisdiction": "National Traffic Code",
            "fine": "Fixed penalty of £300 and 6 penalty points (Court can issue unlimited fine and ban)",
            "points": "6 to 8 points or driving disqualification",
            "full_text": "It is a criminal offense to drive a motor vehicle on a public road without at least third-party vehicle insurance. Police have the power to seize and destroy uninsured vehicles. Penalty is a fixed £300 fine and 6 points, or unlimited fine and court disqualification."
        }
    ]
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_laws, f, indent=2)
