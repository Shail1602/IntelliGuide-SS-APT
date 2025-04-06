import os
import json
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

PDF_FOLDERS = ["pdfs", "Fleet_pdfs"]
JSON_FILE = "scraper/tour_info.json"
EMBED_DB = "embeddings"

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)

all_chunks = []

# ✅ Process PDFs
for folder in PDF_FOLDERS:
    if not os.path.exists(folder): continue
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            with pdfplumber.open(path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if text.strip():
                    chunks = splitter.split_text(text)
                    metadata = [{"source": f"{folder}/{filename}"}] * len(chunks)
                    all_chunks.extend(zip(chunks, metadata))

# ✅ Process tour_info.json
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]  # wrap in list if single record

        for tour in data:
            text_parts = []
            for k, v in tour.items():
                if isinstance(v, list):
                    text_parts.append(f"{k.title().replace('_',' ')}:\n" + "\n".join(map(str, v)))
                else:
                    text_parts.append(f"{k.title().replace('_',' ')}: {v}")
            full_text = "\n".join(text_parts)
            chunks = splitter.split_text(full_text)
            metadata = [{**tour, "source": "tour_info.json"}] * len(chunks)
            all_chunks.extend(zip(chunks, metadata))

# ✅ Save to FAISS
if all_chunks:
    texts, metadatas = zip(*all_chunks)
    db = FAISS.from_texts(texts, embedding, metadatas=metadatas)
    os.makedirs(EMBED_DB, exist_ok=True)
    db.save_local(EMBED_DB)
    print(f"✅ FAISS DB created with {len(texts)} chunks")
else:
    print("⚠️ No data found to index.")
