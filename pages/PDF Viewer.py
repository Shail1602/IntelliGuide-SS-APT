import streamlit as st
import os
import PyPDF2
import re

PDF_DIR = "pdfs"
st.set_page_config(page_title="📚 APT Tour Brochure Library", layout="wide")

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
    .summary-card {
        border: 1px solid #e0e0e0;
        padding: 25px;
        border-radius: 16px;
        background: linear-gradient(to bottom, #ffffff, #f9fbfd);
        margin-bottom: 24px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .summary-card:hover {
        transform: scale(1.01);
    }
    .badge {
        display: inline-block;
        background: #1f77b4;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        margin-right: 6px;
        margin-top: 5px;
    }
    .badge::before {
        content: attr(data-icon); 
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

def tag_icon(tag):
    return {
        "Ocean Cruise": "🛳️",
        "River Cruise": "🚢",
        "Land Tour": "🚍",
        "4WD": "🚙",
        "Europe": "🇪🇺",
        "Asia": "🌏",
        "Australia": "🇦🇺",
        "New Zealand": "🇳🇿",
        "Africa": "🌍",
        "South America": "🌎",
        "General": "📌",
        "Error": "⚠️"
    }.get(tag, "📌")

def extract_pdf_info(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:2]:
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
                "search_blob": f"{title.lower()} {route.group(0).lower() if route else ''} {tags}".lower()
            }
    except Exception:
        return {"title": "N/A", "code": "N/A", "days": "N/A", "route": "N/A", "tags": ["Error"], "search_blob": ""}

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
    filenames = [f[0] for f in current_files]
    file_labels = [f"{info['code']} - {info['title']}" for _, info in current_files]
    selection = st.selectbox("📄 Select a PDF:", options=list(zip(filenames, file_labels)), format_func=lambda x: x[1])
    selected_file, selected_label = selection
    file_path = os.path.join(PDF_DIR, selected_file)
    info = dict([f for f in current_files if f[0] == selected_file][0][1])

    clean_title = re.sub(r'[^\x00-\x7F]+', '', info["title"])

    st.markdown(f"""
    <div class='summary-card'>
      <h3 style='color: #1f3a93;'>🧭 {clean_title}</h3>
      <ul style='font-size:15px; line-height: 1.7; list-style-type: none; padding-left: 0;'>
        <li>📌 <strong>Code:</strong> <span style='color: green;'>{info['code']}</span></li>
        <li>⏱️ <strong>Duration:</strong> {info['days']}</li>
        <li>🚩 <strong>Route:</strong> {info['route']}</li>
        <li>🏷️ <strong>Tags:</strong> {' '.join([f"<span class='badge' data-icon='{tag_icon(tag)}'>{tag}</span>" for tag in info['tags']])}</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    with open(file_path, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name=selected_file)

    if st.checkbox("📄 Show Text Preview (First 3 Pages)"):
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                preview_text = ""
                for i, page in enumerate(reader.pages[:3]):
                    preview_text += f"\n--- Page {i+1} ---\n"
                    preview_text += page.extract_text() or "[No text]"
                st.text_area("📘 PDF Preview", preview_text[:5000] + "\n\n...truncated", height=400)
        except Exception as e:
            st.error(f"❌ Could not read PDF: {e}")
else:
    st.warning("No PDF files match your search.")
