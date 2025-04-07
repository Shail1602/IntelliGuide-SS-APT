import os
import json
import pdfplumber
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 📁 Paths
PDF_FOLDERS = ["pdfs", "Fleet_pdfs"]
JSON_FILE = "scraper/tour_info.json"
EMBED_DB = "embeddings"

# 🔍 Embedding model and text splitter
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# 🧩 Collected Chunks
all_chunks = []

# 📘 Load tour JSON data and build lookup
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

# 📄 Process PDFs and attach metadata
for folder in PDF_FOLDERS:
    if not os.path.exists(folder):
        continue
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            file_key = filename.replace(" ", "_").lower()
            tour_meta = tour_lookup.get(file_key, {})
            tour_meta_enriched = {
                "source": f"{folder}/{filename}",
                "trip_name": tour_meta.get("Trip Name", "Unknown"),
                "trip_code": tour_meta.get("Trip Code", "Unknown"),
                "region": tour_meta.get("Region", "Unknown"),
                "country": tour_meta.get("Country", "Unknown"),
            }

            with pdfplumber.open(path) as pdf:
                raw_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if raw_text.strip():
                    chunks = splitter.split_text(raw_text)
                    metadata = [tour_meta_enriched] * len(chunks)
                    all_chunks.extend(zip(chunks, metadata))

# 📘 Also embed full JSON tour info as text
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
            chunks = splitter.split_text(full_text)
            metadata = [{**tour, "source": "tour_info.json"}] * len(chunks)
            all_chunks.extend(zip(chunks, metadata))

# 💾 Save to FAISS
if all_chunks:
    texts, metadatas = zip(*all_chunks)
    db = FAISS.from_texts(texts, embedding, metadatas=metadatas)
    os.makedirs(EMBED_DB, exist_ok=True)
    db.save_local(EMBED_DB)
    print(f"✅ FAISS index created with {len(texts)} chunks and saved to '{EMBED_DB}'")
else:
    print("⚠️ No data found to index.")
