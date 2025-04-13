import os
import json
import pdfplumber
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pydantic

print("✅ Vector DB using pydantic version:", pydantic.__version__)

#  Paths
PDF_FOLDERS = ["pdfs", "Fleet_pdfs"]
JSON_FILE = "scraper/tour_info.json"
EMBED_DB = "embeddings"

#  Embedding model and text splitter
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

#  Collected Chunks
all_chunks = []

# 🧹 Helper to clean PDF text
def clean_text(text):
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

#  Load tour JSON data and build lookup
tour_lookup = {}
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for tour in data:
            file_key = (
                tour.get("filename") or
                tour.get("pdf_name") or
                (tour.get("tour_code") + ".pdf" if tour.get("tour_code") else None)
            )
            if file_key:
                tour_lookup[file_key.replace(" ", "_").lower()] = tour

#  Process PDFs and attach metadata
for folder in PDF_FOLDERS:
    if not os.path.exists(folder):
        continue
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            file_key = filename.replace(" ", "_").lower()
            tour_meta = tour_lookup.get(file_key, {})
            enriched_text_header = f"Trip Code: {tour_meta.get('Trip Code', 'Unknown')}\nTrip Name: {tour_meta.get('Trip Name', 'Unknown')}\n"
            tour_meta_enriched = {
                "source": f"{folder}/{filename}",
                "trip_name": tour_meta.get("Trip Name", "Unknown"),
                "trip_code": tour_meta.get("Trip Code", "Unknown"),
                "region": tour_meta.get("Region", "Unknown"),
                "country": tour_meta.get("Country", "Unknown"),
                "trip_type": tour_meta.get("Trip Type", ""),
                "highlights": ", ".join(tour_meta.get("Highlights", [])) if isinstance(tour_meta.get("Highlights"), list) else "",
                "booking_url": tour_meta.get("booking_url", ""),
                "start_date": tour_meta.get("start_date", ""),
                "end_date": tour_meta.get("end_date", ""),
                "duration": tour_meta.get("duration", ""),
                "price": tour_meta.get("price", ""),
                "source_file": filename,
                "indexed_on": datetime.now().isoformat()
            }

            with pdfplumber.open(path) as pdf:
                raw_text = clean_text("\n".join([page.extract_text() or "" for page in pdf.pages]))
                if raw_text.strip():
                    chunks = splitter.split_text(enriched_text_header + raw_text)
                    metadata = [tour_meta_enriched] * len(chunks)
                    all_chunks.extend(zip(chunks, metadata))

#  Also embed full JSON tour info as text
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for tour in data:
            text_parts = []
            for k, v in tour.items():
                if isinstance(v, list):
                    v_clean = "\n".join([f"- {item}" for item in v])
                    text_parts.append(f"{k.replace('_', ' ').title()}:\n{v_clean}")
                else:
                    text_parts.append(f"{k.replace('_', ' ').title()}: {v}")
            full_text = "\n".join(text_parts)
            header = f"Trip Code: {tour.get('Trip Code', 'Unknown')}\nTrip Name: {tour.get('Trip Name', 'Unknown')}\n"
            chunks = splitter.split_text(header + clean_text(full_text))
            enriched_meta = {**tour, "source": "tour_info.json", "indexed_on": datetime.now().isoformat()}
            metadata = [enriched_meta] * len(chunks)
            all_chunks.extend(zip(chunks, metadata))

#  Save to FAISS
if all_chunks:
    texts, metadatas = zip(*all_chunks)
    db = FAISS.from_texts(texts, embedding, metadatas=metadatas)
    os.makedirs(EMBED_DB, exist_ok=True)
    db.save_local(EMBED_DB)
    print("✅ FAISS index created with", len(texts), "chunks and saved to '", EMBED_DB, "'")
    print("📊 Indexing Summary:")
    print(" - Unique Files:", len(set(m['source'] for m in metadatas)))
    print(" - Metadata Fields:", list(metadatas[0].keys()) if metadatas else [])
else:
    print("⚠️ No data found to index.")
