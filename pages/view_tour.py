import streamlit as st
import json
import os

# --- App Config & Branding ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Admin", page_icon="🌏")

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
        tours = data if isinstance(data, list) else [data]

# --- Search ---
search_term = st.text_input("🔎 Search by trip name, code, region, or country").lower()
filtered_tours = [
    t for t in tours if any(search_term in str(t.get(k, "")).lower() for k in ["trip_name", "trip_code", "region", "country"])
]

# --- Style ---
st.markdown("""
    <style>
        .tour-card {
            background-color: #f9fbfd;
            border: 1px solid #e1e8ed;
            border-radius: 12px;
            padding: 25px 30px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .tour-card:hover {
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }
        .field-label {
            font-weight: 600;
            margin-top: 15px;
            font-size: 15px;
        }
        .save-button {
            background-color: #1f77b4 !important;
            color: white !important;
            font-weight: 600;
            margin-top: 10px;
        }
        .tag {
            display: inline-block;
            background: #e0f7fa;
            color: #007c91;
            font-size: 12px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 6px;
            margin-right: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Display Cards ---
for i, tour in enumerate(filtered_tours):
    st.markdown('<div class="tour-card">', unsafe_allow_html=True)

    # Top info
    st.markdown(f"### 📌 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})")
    st.markdown(
        f"<span class='tag'>🌍 {tour.get('region', 'Unknown')}</span>"
        f"<span class='tag'>📍 {tour.get('country', 'Unknown')}</span>", unsafe_allow_html=True
    )

    st.markdown(f"🔗 **Original**: [{tour.get('original_url')}]({tour.get('original_url')})")
    if tour.get("booking_url"):
        st.markdown(f"🔗 **Booking**: [{tour.get('booking_url')}]({tour.get('booking_url')})")

    # Inclusions
    if tour.get("trip_inclusions"):
        st.markdown("**📋 Key Inclusions:**")
        st.markdown("<ul style='margin-top: -10px;'>", unsafe_allow_html=True)
        for inc in tour["trip_inclusions"][:5]:
            st.markdown(f"<li>{inc}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    # Editable Inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📅 Start Date**", unsafe_allow_html=True)
        tour["start_date"] = st.text_input("", value=tour.get("start_date", ""), key=f"start_{i}")
    with col2:
        st.markdown("**📅 End Date**", unsafe_allow_html=True)
        tour["end_date"] = st.text_input("", value=tour.get("end_date", ""), key=f"end_{i}")
    with col3:
        st.markdown("**💰 Price (AUD)**", unsafe_allow_html=True)
        tour["price_aud"] = st.text_input("", value=tour.get("price_aud", ""), key=f"price_{i}")

    tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{i}")

    # Save Button
    if st.button("💾 Save Changes", key=f"save_{i}"):
        with open(json_file, "w") as f:
            json.dump(tours, f, indent=2)
        st.success("✅ Tour info updated!")

    st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 30px;">
    <div style='text-align: center; font-size: 13px; color: #888;'>SS IntelliGuide • Designed by Shailesh & Saumya</div>
""", unsafe_allow_html=True)
