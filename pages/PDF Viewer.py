import streamlit as st
import os
import PyPDF2
import re

PDF_DIR = "pdfs"
st.set_page_config(page_title="📚 APT Tour Brochure Library", layout="wide")
st.title("🌍 APT Tour PDF Library")


search_code = st.text_input("🔍 Search by Tour Code or Filename (e.g., EUSST11):").strip().lower()
pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])
filtered_files = [f for f in pdf_files if search_code in f.lower()] if search_code else pdf_files


page_size = 15
total_pages = max(1, (len(filtered_files) - 1) // page_size + 1)
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

start = (page - 1) * page_size
end = start + page_size
current_files = filtered_files[start:end]


def extract_pdf_info(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:2]:  # Only first 2 pages for speed
                text += page.extract_text() or ""

            # Extract key info
            code = re.search(r"\b[A-Z]{3,}\d{2,}\b", text)
            days = re.search(r"\b\d+\s+days?\s*/\s*\d+\s+nights?\b", text, re.IGNORECASE)
            route = re.search(r"(\b\w+ to \w+\b)", text)
            title = text.strip().split("\n")[0][:80]

            
            tags = []
            for tag in ["Ocean Cruise", "River Cruise", "Asia", "Europe", "Australia", "New Zealand", "Africa", "South America"]:
                if tag.lower() in text.lower():
                    tags.append(tag)

            return {
                "title": title,
                "code": code.group(0) if code else "N/A",
                "days": days.group(0) if days else "N/A",
                "route": route.group(0) if route else "N/A",
                "tags": tags or ["General"]
            }
    except Exception as e:
        return {"title": "N/A", "code": "N/A", "days": "N/A", "route": "N/A", "tags": ["Error reading file"]}


if current_files:
    selected_file = st.selectbox("📄 Select a PDF:", current_files)
    file_path = os.path.join(PDF_DIR, selected_file)

    
    info = extract_pdf_info(file_path)

  
    st.markdown(f"""
    ### 🧭 {info['title']}
    - 📌 **Code**: `{info['code']}`
    - ⏱️ **Duration**: {info['days']}
    - 🚩 **Route**: {info['route']}
    - 🏷️ **Tags**: {' | '.join(info['tags'])}
    """)

   
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
