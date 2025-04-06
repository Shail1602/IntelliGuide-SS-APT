import os
import json
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

PDF_FOLDERS = ["pdfs", "Fleet_pdfs"]
JSON_FILE = "scraper/tour_info.json"
EMBED_DB = "embeddings"

# Embedder and text splitter
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)
all_chunks = []

# Process PDFs
for folder in PDF_FOLDERS:
    if not os.path.exists(folder):
        continue
    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            path = os.path.join(folder, file)
            with pdfplumber.open(path) as pdf:
                text = " ".join([page.extract_text() or "" for page in pdf.pages])
                chunks = splitter.split_text(text)
                metadatas = [{"source": f"{folder}/{file}", "file_name": file}] * len(chunks)
                all_chunks.extend(zip(chunks, metadatas))

# Process tour_info.json
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for tour in data:
            text_lines = []
            metadata = {"source": "tour_info.json"}
            for k, v in tour.items():
                value = "\n".join(v) if isinstance(v, list) else str(v)
                text_lines.append(f"{k.title().replace('_', ' ')}: {value}")
                metadata[k] = value
            chunks = splitter.split_text("\n".join(text_lines))
            metadatas = [metadata] * len(chunks)
            all_chunks.extend(zip(chunks, metadatas))

# Save to FAISS
if all_chunks:
    texts, metas = zip(*all_chunks)
    db = FAISS.from_texts(texts, embedding, metadatas=metas)
    os.makedirs(EMBED_DB, exist_ok=True)
    db.save_local(EMBED_DB)
    print(f"✅ FAISS index built with {len(texts)} chunks and saved to '{EMBED_DB}'")
else:
    print("⚠️ No content found to build FAISS index.")
