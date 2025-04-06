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

# 📄 Process PDFs
for folder in PDF_FOLDERS:
    if not os.path.exists(folder):
        continue
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            with pdfplumber.open(path) as pdf:
                raw_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if raw_text.strip():
                    chunks = splitter.split_text(raw_text)
                    metadata = [{"source": f"{folder}/{filename}"}] * len(chunks)
                    all_chunks.extend(zip(chunks, metadata))

# 📘 Process JSON tours
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]  # wrap single object

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
