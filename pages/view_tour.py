
import streamlit as st
import json
import os

# --- App Config ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- Custom CSS ---
st.markdown("""
    <style>
    .tour-card {
        background-color: #fff;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 25px 30px;
        margin-bottom: 30px;
        transition: all 0.3s ease;
        border-left: 6px solid #1f77b4;
    }
    .tour-card:hover {
        box-shadow: 0 8px 18px rgba(0,0,0,0.08);
        transform: translateY(-4px);
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        background-color: #e0f2fe;
        color: #0369a1;
        border-radius: 16px;
        font-size: 12px;
        margin-right: 8px;
        margin-bottom: 4px;
    }
    .section-title {
        font-weight: 600;
        font-size: 15px;
        color: #444;
        margin-top: 18px;
    }
    .stTextInput>div>div>input {
        background-color: #f8fafc;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("### 🌏 SS IntelliGuide – APT Tour Admin")
    st.markdown("##### Manage, Search & Edit Tours – backed by AI & Travel Intelligence")
with col2:
    st.image("https://raw.githubusercontent.com/Shail1602/Inellibot/main/dbr.jpg", width=60)

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

# --- Search ---
search_term = st.text_input("🔍 Search by trip name, code, region, or country").lower()
filtered_tours = [
    tour for tour in tours 
    if isinstance(tour, dict) and search_term in tour.get("trip_name", "").lower()
    or search_term in tour.get("trip_code", "").lower()
    or search_term in tour.get("region", "").lower()
    or search_term in tour.get("country", "").lower()
]

# --- Pagination ---
tours_per_page = 15
total_pages = (len(filtered_tours) - 1) // tours_per_page + 1
current_page = st.number_input("📄 Page", min_value=1, max_value=total_pages, step=1)
start_idx = (current_page - 1) * tours_per_page
end_idx = start_idx + tours_per_page
paged_tours = filtered_tours[start_idx:end_idx]

# --- Tour Cards in Grid (3 per row) ---
rows = [paged_tours[i:i+3] for i in range(0, len(paged_tours), 3)]
for row in rows:
    cols = st.columns(3)
    for idx, tour in enumerate(row):
        if not isinstance(tour, dict) or "trip_code" not in tour:
            continue
        with cols[idx]:
            st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
            st.markdown(f"### 📌 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})", unsafe_allow_html=True)
            st.markdown(" ".join([
                f"<span class='badge'>{tour.get('region', '')}</span>",
                f"<span class='badge'>{tour.get('country', '')}</span>"
            ]), unsafe_allow_html=True)

            # URLs
            st.markdown(f"🔗 **Original**: [{tour.get('original_url', '')}]({tour.get('original_url', '')})")
            if tour.get('booking_url'):
                st.markdown(f"🔗 **Booking**: [{tour.get('booking_url')}]({tour.get('booking_url')})")

            # Inclusions as tags (Top 3 keywords)
            if tour.get("trip_inclusions"):
                st.markdown("**🧭 Highlights:**", unsafe_allow_html=True)
                selected = [inc for inc in tour["trip_inclusions"] if len(inc.split()) <= 6][:3]
                st.markdown("".join([f"<span class='badge'>{x}</span>" for x in selected]), unsafe_allow_html=True)

            st.markdown("**📅 Tour Details**")
            st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
            st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
            st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")

            st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")

            if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
                for t in tours:
                    if t.get("trip_code") == tour.get("trip_code"):
                        t.update(tour)
                with open(json_file, "w") as f:
                    json.dump(tours, f, indent=2)
                st.success("✅ Tour info updated!")

            st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 30px; margin-bottom: 10px;">
    <div style='text-align: center; font-size: 13px; color: #888; margin-top: 10px;'>
      SS IntelliGuide • Designed by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
