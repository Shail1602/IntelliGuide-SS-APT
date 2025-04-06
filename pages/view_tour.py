import streamlit as st
import json
import os
import re

# --- App Config ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- CSS Styling ---
st.markdown("""
    <style>
    .banner {
        background: linear-gradient(to right, #0ea5e9, #38bdf8);
        color: white;
        padding: 25px 40px;
        border-radius: 12px;
        margin-bottom: 25px;
    }
    .tour-card {
        background-color: #fff;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px 24px;
        margin-bottom: 25px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        background-color: #e0f2fe;
        color: #0369a1;
        border-radius: 12px;
        font-size: 11px;
        margin: 2px 6px 6px 0;
    }
    .section-title {
        font-weight: 600;
        font-size: 13px;
        color: #444;
        margin-top: 12px;
        margin-bottom: 4px;
    }
    .stTextInput>div>div>input {
        background-color: #f8fafc;
    }
    </style>
""", unsafe_allow_html=True)

# --- Banner Header ---
st.markdown("""
    <div class="banner">
        <h2>🌏 SS IntelliGuide – Tour Editor</h2>
        <p style='margin:0;'>Manage, Search & Edit Luxury Tours – backed by AI & Travel Intelligence</p>
    </div>
""", unsafe_allow_html=True)

# --- Load Tour JSON ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search Bar ---
search_term = st.text_input("🔍 Search by trip name, code, region, or country").lower()
filtered_tours = [
    tour for tour in tours
    if search_term in tour.get("trip_name", "").lower()
    or search_term in tour.get("trip_code", "").lower()
    or search_term in tour.get("region", "").lower()
    or search_term in tour.get("country", "").lower()
]

# --- Keywords for Tags ---
tag_keywords = ["luxury", "cruise", "meals", "drinks", "excursion", "transfer", "accommodation", "flight", "dining"]

# --- Display in 3 columns layout ---
rows = [filtered_tours[i:i+3] for i in range(0, len(filtered_tours), 3)]
for row in rows:
    cols = st.columns(3)
    for tour, col in zip(row, cols):
        with col:
            st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
            st.markdown(f"### 🔖 {tour.get('trip_name')} ({tour.get('trip_code')})", unsafe_allow_html=True)

            # Badges
            region = tour.get("region", "")
            country = tour.get("country", "")
            inclusion_text = " ".join(tour.get("trip_inclusions", []))
            tags = [word for word in tag_keywords if re.search(rf"\\b{word}\\b", inclusion_text, re.IGNORECASE)]
            badges_html = "".join([f"<span class='badge'>{b}</span>" for b in [region, country] + tags])
            st.markdown(badges_html, unsafe_allow_html=True)

            # URLs
            if tour.get("original_url"):
                st.markdown(f"🔗 **Original**: [{tour['original_url']}]({tour['original_url']})")
            if tour.get("booking_url"):
                st.markdown(f"🔗 **Booking**: [{tour['booking_url']}]({tour['booking_url']})")

            # Key Inclusions – Hidden to keep concise
            # st.markdown("<div class='section-title'>📋 Inclusions</div>", unsafe_allow_html=True)
            # st.markdown("\n".join([f"- {i}" for i in tour.get("trip_inclusions", [])]))

            # Editable Fields
            st.markdown("<div class='section-title'>📅 Tour Details</div>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                tour["start_date"] = st.text_input("Start Date", tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
            with d2:
                tour["end_date"] = st.text_input("End Date", tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
            with d3:
                tour["price_aud"] = st.text_input("Price (AUD)", tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")

            # Checkbox + Save Button
            tour["limited_availability"] = st.checkbox("🔴 Limited Availability", tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")
            if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
                with open(json_file, "w") as f:
                    json.dump(tours, f, indent=2)
                st.success("✅ Tour updated!")

            st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 30px;">
    <div style='text-align: center; font-size: 13px; color: #999;'>SS IntelliGuide • Designed by Shailesh & Saumya</div>
""", unsafe_allow_html=True)
