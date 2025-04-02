import streamlit as st
import os
import PyPDF2
import re

PDF_DIR = "pdfs"
st.set_page_config(page_title="📚 APT Tour Brochure Library", layout="wide")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "selected_pdf" not in st.session_state:
    st.session_state.selected_pdf = None

# Sidebar toggle for Dark Mode
with st.sidebar:
    st.toggle("🌃 Dark Mode", key="dark_mode")

# Dynamic theme based on Dark Mode
if st.session_state.dark_mode:
    st.markdown("""
        <style>
        body, .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .card, .modal {
            background-color: #1f1f1f;
            color: #fafafa;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body, .stApp {
            background-color: #f6f9fc;
            color: #111;
        }
        .card, .modal {
            background-color: white;
            color: #111;
        }
        </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div style='background-image: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e"); 
                background-size: cover; 
                background-position: center; 
                padding: 30px; border-radius: 16px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
                margin-bottom: 30px; color: white;'>
        <h1 style='font-size: 38px; margin-bottom: 5px;'>🌍 APT Tour PDF Library</h1>
        <p style='font-size: 18px;'>Curated luxury tours, now just a click away.</p>
    </div>
""", unsafe_allow_html=True)

search_query = st.text_input("🔍 Search by code, title, or location (e.g., Broome, Darwin, Safari):").strip().lower()

st.markdown("""
    <style>
    .card {
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
        margin: 10px;
        transition: all 0.3s ease;
        min-height: 430px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card:hover {
        box-shadow: 0 4px 14px rgba(0,0,0,0.2);
        transform: scale(1.01);
    }
    .badge {
        display: inline-block;
        background: #1f77b4;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        margin: 4px 4px 4px 0;
    }
    </style>
""", unsafe_allow_html=True)

def extract_pdf_info(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:3]:
                text += page.extract_text() or ""
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)

            title = text.strip().split("\n")[0][:80]
            code = re.search(r"\b[A-Z]{3,}\d{2,}\b", text)
            days = re.search(r"\b\d+\s+days?\s*/\s*\d+\s+nights?\b", text, re.IGNORECASE)
            route = re.search(r"(\b\w+ to \w+\b)", text)

            tags = []
            for tag in ["Ocean Cruise", "River Cruise", "Land Tour", "4WD", "Europe", "Asia", "Australia", "New Zealand", "Africa", "South America"]:
                if tag.lower() in text.lower():
                    tags.append(tag)

            return {
                "title": title,
                "code": code.group(0) if code else "N/A",
                "days": days.group(0) if days else "N/A",
                "route": route.group(0) if route else "N/A",
                "tags": tags or ["General"],
                "search_blob": f"{title.lower()} {route.group(0).lower() if route else ''} {tags}".lower(),
                "text_preview": text[:1000]  # Shorter preview
            }
    except Exception:
        return {"title": "N/A", "code": "N/A", "days": "N/A", "route": "N/A", "tags": ["Error"], "search_blob": "", "text_preview": ""}

pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])
indexed_files = [(f, extract_pdf_info(os.path.join(PDF_DIR, f))) for f in pdf_files]
filtered = [item for item in indexed_files if search_query in item[1]["search_blob"] or search_query in item[0].lower()] if search_query else indexed_files

page_size = 15
total_pages = max(1, (len(filtered) - 1) // page_size + 1)
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
start = (page - 1) * page_size
end = start + page_size
current_files = filtered[start:end]

if current_files:
    rows = [st.columns(3) for _ in range((len(current_files) + 2) // 3)]
    for idx, (filename, info) in enumerate(current_files):
        file_path = os.path.join(PDF_DIR, filename)
        clean_title = re.sub(r'[^\x00-\x7F]+', '', info["title"])
        col = rows[idx // 3][idx % 3]
        with col:
            with st.container():
                st.markdown(f"""
                <div class='card'>
                    <div>
                        <strong>📄 {info['code']} – {clean_title}</strong><br>
                        <small>⏱️ {info['days']} | 🚩 {info['route']}</small><br>
                        <div style='margin-top: 6px; display: flex; flex-wrap: wrap;'>{' '.join([f"<span class='badge'>{tag}</span>" for tag in info['tags']])}</div>
                        <div style='margin-top: 12px;'>
                            <strong>Preview:</strong>
                            <div style='font-size: 13px; white-space: pre-wrap; max-height: 100px; overflow-y: auto;'>{info['text_preview']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                with open(file_path, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=filename, key=f"dl_{filename}")
                st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No PDF files match your search.")
