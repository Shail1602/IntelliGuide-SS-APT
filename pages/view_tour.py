import streamlit as st
import json
import os

# --- App Config ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- Custom CSS for Enhanced UI ---
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
    }
    .section-title {
        font-weight: 600;
        font-size: 15px;
        color: #444;
        margin-top: 18px;
        margin-bottom: 10px;
    }
    .card-row {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 10px;
    }
    .card-input {
        flex: 1;
    }
    .card-input label {
        font-weight: 500;
        font-size: 13px;
        color: #555;
    }
    .styled-input input {
        width: 100%;
        padding: 8px 12px;
        font-size: 14px;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: #f8fafc;
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
    if search_term in tour.get("trip_name", "").lower()
    or search_term in tour.get("trip_code", "").lower()
    or search_term in tour.get("region", "").lower()
    or search_term in tour.get("country", "").lower()
]

# --- Tour Display ---
for tour in filtered_tours:
    st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
    st.markdown(f"### 🔖 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})", unsafe_allow_html=True)
    
    # Badges
    badges = f"""
        <span class="badge">{tour.get('region', '')}</span>
        <span class="badge">{tour.get('country', '')}</span>
    """
    st.markdown(badges, unsafe_allow_html=True)

    # URLs
    st.markdown(f"🔗 **Original**: [{tour.get('original_url', '')}]({tour.get('original_url', '')})")
    if tour.get('booking_url'):
        st.markdown(f"🔗 **Booking**: [{tour.get('booking_url')}]({tour.get('booking_url')})")

    # Inclusions
    if tour.get("trip_inclusions"):
        st.markdown("<div class='section-title'>📋 Key Inclusions:</div>", unsafe_allow_html=True)
        st.markdown("\n".join([f"- {item}" for item in tour.get("trip_inclusions", [])]))

    # Tour Details
    st.markdown("<div class='section-title'>📅 Tour Details:</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-row'>", unsafe_allow_html=True)

    # Input boxes with hidden labels
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            tour["start_date"] = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
        with col2:
            tour["end_date"] = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
        with col3:
            tour["price_aud"] = st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Limited availability checkbox
    tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")

    # Save button
    if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
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
