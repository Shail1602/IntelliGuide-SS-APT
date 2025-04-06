import streamlit as st
import json
import os
import math

# --- Config ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- Custom Styles ---
st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(to right, #0077b6, #48cae4);
            padding: 30px 25px;
            border-radius: 12px;
            color: white;
            margin-bottom: 25px;
        }
        .tour-card {
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 22px;
            margin-bottom: 25px;
            border: 1px solid #e6e6e6;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            background-color: #e0f2fe;
            color: #0369a1;
            border-radius: 16px;
            font-size: 12px;
            margin: 4px 6px 6px 0;
        }
        .highlight-badge {
            background-color: #d1fae5;
            color: #065f46;
        }
        .section-label {
            margin-top: 15px;
            font-weight: 600;
            color: #444;
        }
        input {
            background-color: #f9fafb !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Banner ---
st.markdown("""
<div class="header-banner">
    <h3>🌏 SS IntelliGuide – APT Tour Admin</h3>
    <p style="margin: 0;">Manage, Search & Edit Tours – backed by AI & Travel Intelligence</p>
</div>
""", unsafe_allow_html=True)

# --- Load JSON ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        if isinstance(data, list):
            tours = data
        elif isinstance(data, dict):
            tours.append(data)

# --- Search & Pagination (in one row) ---
col_search, col_page = st.columns([4, 1])
with col_search:
    search_term = st.text_input("🔍 Search by trip name, code, region, or country").lower()

with col_page:
    total_pages = math.ceil(len(tours) / 15)
    page = st.number_input("📄 Page", min_value=1, max_value=max(1, total_pages), step=1)

# --- Filtered & Paginated Tours ---
filtered = [
    t for t in tours if search_term in t.get("trip_name", "").lower()
    or search_term in t.get("trip_code", "").lower()
    or search_term in t.get("region", "").lower()
    or search_term in t.get("country", "").lower()
]

start_index = (page - 1) * 15
end_index = start_index + 15
paged_tours = filtered[start_index:end_index]

# --- Helper: Get Highlight Tags from Inclusions ---
def extract_tags(inclusions):
    if not inclusions:
        return []
    keywords = ['experiences', 'hand-picked', 'meals', 'tipping', 'cruise', 'transfer']
    tags = []
    for inc in inclusions:
        for k in keywords:
            if k.lower() in inc.lower():
                tags.append(inc.split(",")[0][:40] + "...")
                break
    return tags[:3]

# --- Display Tours in Grid ---
for i in range(0, len(paged_tours), 3):
    row = st.columns(3)
    for j, tour in enumerate(paged_tours[i:i+3]):
        with row[j]:
            st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
            st.markdown(f"### 📌 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})", unsafe_allow_html=True)

            # Region + Country badges
            st.markdown("".join([
                f"<span class='badge'>{tour.get('region', '')}</span>",
                f"<span class='badge'>{tour.get('country', '')}</span>"
            ]), unsafe_allow_html=True)

            # URLs
            st.markdown(f"🔗 <b>Original:</b> [{tour.get('original_url', '')}]({tour.get('original_url', '')})", unsafe_allow_html=True)
            if tour.get("booking_url"):
                st.markdown(f"🔗 <b>Booking:</b> [{tour.get('booking_url', '')}]({tour.get('booking_url', '')})", unsafe_allow_html=True)

            # Tags
            tags = extract_tags(tour.get("trip_inclusions", []))
            if tags:
                st.markdown("<span style='color:#92400e; font-weight:600;'>🔅 Highlights:</span>", unsafe_allow_html=True)
                for tag in tags:
                    st.markdown(f"<span class='badge highlight-badge'>{tag}</span>", unsafe_allow_html=True)

            # Editable Fields
            st.markdown("<div class='section-label'>🗂️ Tour Details</div>", unsafe_allow_html=True)
            tour["start_date"] = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
            tour["end_date"] = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
            tour["price_aud"] = st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")
            tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")

            # Save Button
            if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
                with open(json_file, "w") as f:
                    json.dump(tours, f, indent=2)
                st.success("✅ Tour info updated!")

            st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<hr style="margin-top: 40px;">
<div style='text-align: center; font-size: 13px; color: #888;'>
    SS IntelliGuide • Designed by Shailesh & Saumya
</div>
""", unsafe_allow_html=True)
