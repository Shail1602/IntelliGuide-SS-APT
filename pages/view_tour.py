
import streamlit as st
import json
import os
import math

# --- Page Config ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- CSS Styling ---
st.markdown("""
    <style>
    .tour-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: all 0.3s ease-in-out;
    }
    .tour-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .badge {
        display: inline-block;
        padding: 5px 10px;
        margin: 2px 4px 6px 0;
        border-radius: 20px;
        font-size: 11px;
        background-color: #e0f2fe;
        color: #0369a1;
    }
    .highlight-badge {
        background-color: #d1fae5;
        color: #047857;
    }
    .header-banner {
        background: linear-gradient(to right, #0284c7, #0ea5e9);
        padding: 25px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        color: white;
    }
    .header-banner h2 {
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Banner Header ---
st.markdown("""
<div class='header-banner'>
    <h2>🌏 SS IntelliGuide – APT Tour Admin</h2>
    <p>Manage, Search & Edit Tours – backed by AI & Travel Intelligence</p>
</div>
""", unsafe_allow_html=True)

# --- Load JSON Data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search + Page Controls ---
col_search, col_page = st.columns([4, 1])
with col_search:
    search_term = st.text_input("🔍 Search by trip name, code, region, or country").lower()
with col_page:
    page = st.number_input("📄 Page", min_value=1, value=1, step=1)

# --- Filtered + Paginated Tours ---
filtered = [
    t for t in tours
    if search_term in t.get("trip_name", "").lower()
    or search_term in t.get("trip_code", "").lower()
    or search_term in t.get("region", "").lower()
    or search_term in t.get("country", "").lower()
]

per_page = 15
start_idx = (page - 1) * per_page
end_idx = start_idx + per_page
visible_tours = filtered[start_idx:end_idx]

# --- Helper for Keywords from Inclusions ---
def extract_keywords(inclusions, limit=3):
    keywords = []
    for inc in inclusions or []:
        words = inc.split()
        if "experience" in inc.lower() or "night" in inc.lower() or "transfer" in inc.lower():
            keywords.append(" ".join(words[:4]))
        elif len(words) >= 2:
            keywords.append(" ".join(words[:2]))
        if len(keywords) >= limit:
            break
    return keywords

# --- Render Tour Cards ---
for i in range(0, len(visible_tours), 3):
    row = st.columns(3)
    for j in range(3):
        if i + j >= len(visible_tours): break
        tour = visible_tours[i + j]
        with row[j]:
            st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
            st.markdown(f"### 📌 {tour.get('trip_name')} ({tour.get('trip_code')})")

            st.markdown("".join([
                f"<span class='badge'>{tour.get('region', '')}</span>",
                f"<span class='badge'>{tour.get('country', '')}</span>"
            ]), unsafe_allow_html=True)

            st.markdown(f"🔗 <b>Original:</b> <a href='{tour.get('original_url')}' target='_blank'>{tour.get('original_url')}</a>", unsafe_allow_html=True)
            st.markdown(f"🔗 <b>Booking:</b> <a href='{tour.get('booking_url')}' target='_blank'>{tour.get('booking_url')}</a>", unsafe_allow_html=True)

            highlights = extract_keywords(tour.get("trip_inclusions", []))
            if highlights:
                st.markdown("🟡 <b>Highlights:</b>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge highlight-badge'>{k}</span>" for k in highlights]), unsafe_allow_html=True)

            st.markdown("📋 <b>Tour Details</b>", unsafe_allow_html=True)
            tour["start_date"] = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
            tour["end_date"] = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
            tour["price_aud"] = st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")
            tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")
            if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
                with open(json_file, "w") as f:
                    json.dump(tours, f, indent=2)
                st.success("✅ Tour info updated!")
            st.markdown("</div>", unsafe_allow_html=True)
