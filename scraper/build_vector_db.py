import os
import json
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

# Paths
PDF_FOLDERS = ["pdfs", "Fleet_pdfs"]
JSON_FILE = "scraper/tour_info.json"
EMBED_DB = "embeddings"

# Initialize embedding and chunking
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)

all_chunks = []

# ✅ Process PDF files
for folder in PDF_FOLDERS:
    if not os.path.exists(folder):
        continue
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            with pdfplumber.open(path) as pdf:
                text = " ".join([page.extract_text() or "" for page in pdf.pages])
                chunks = splitter.split_text(text)
                metadatas = [{"source": f"{folder}/{filename}"}] * len(chunks)
                all_chunks.extend(zip(chunks, metadatas))

# ✅ Process JSON file (tour_info.json)
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]  # wrap in list if only one record

        for tour in data:
            text_parts = []
            for key in ["trip_name", "trip_code", "region", "country", "description"]:
                if tour.get(key):
                    text_parts.append(f"{key.title().replace('_', ' ')}: {tour[key]}")
            inclusions = tour.get("trip_inclusions", [])
            if inclusions:
                text_parts.append("Trip Inclusions:\n" + "\n".join(inclusions))

            text = "\n".join(text_parts)
            chunks = splitter.split_text(text)
            metadatas = [{"source": "tour_info.json", "trip_name": tour.get("trip_name", "")}] * len(chunks)
            all_chunks.extend(zip(chunks, metadatas))

# ✅ Save to FAISS
if all_chunks:
    texts, metadatas = zip(*all_chunks)
    db = FAISS.from_texts(texts, embedding, metadatas=metadatas)
    os.makedirs(EMBED_DB, exist_ok=True)
    db.save_local(EMBED_DB)
    print(f"✅ FAISS index built with {len(texts)} chunks and saved to '{EMBED_DB}'")
else:
    print("⚠️ No content found to build FAISS index.")
