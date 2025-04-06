import streamlit as st
import json
import os

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – APT Tour Cards", page_icon="🌏")

# --- Header Banner ---
st.markdown("""
    <div style="background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e'); 
                background-size: cover; background-position: center;
                padding: 30px; border-radius: 16px; color: white;
                font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
        <h2>🌏 APT Tour Library</h2>
        <p>Manage, search & edit luxury tours — just a click away.</p>
    </div>
    <br>
""", unsafe_allow_html=True)

# --- Load Data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search Box ---
search_term = st.text_input("🔍 Search by code, name, region, or country").strip().lower()

filtered_tours = [
    t for t in tours
    if search_term in t.get("trip_name", "").lower()
    or search_term in t.get("trip_code", "").lower()
    or search_term in t.get("region", "").lower()
    or search_term in t.get("country", "").lower()
]

# --- Style for Cards ---
st.markdown("""
    <style>
    .card {
        background-color: #fff;
        border: 1px solid #eee;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    }
    .badge {
        display: inline-block;
        background: #e0f7fa;
        color: #00796b;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 12px;
        margin-right: 6px;
    }
    .label {
        font-weight: 600;
        margin-right: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Display Cards ---
cols = st.columns(2)
for idx, tour in enumerate(filtered_tours):
    with cols[idx % 2]:
        st.markdown(f"""
        <div class="card">
            <h4>📌 {tour.get("trip_name", "")} <span style='color: #666;'>({tour.get("trip_code", "")})</span></h4>
            <div>
                <span class="badge">{tour.get("region", "").capitalize()}</span>
                <span class="badge">{tour.get("country", "").capitalize()}</span>
            </div>
            <p style="margin-top:10px;">
                <span class="label">🌐 Original:</span> 
                <a href="{tour.get("original_url", "")}" target="_blank">{tour.get("original_url", "")}</a><br>
                <span class="label">🛒 Booking:</span> 
                <a href="{tour.get("booking_url", "")}" target="_blank">{tour.get("booking_url", "")}</a>
            </p>
            <p><strong>📋 Key Inclusions:</strong></p>
            <ul style="font-size: 14px;">
                {''.join([f"<li>{inc}</li>" for inc in tour.get("trip_inclusions", []) if inc.lower() != "title"])}
            </ul>
            <div style="margin-top:10px;">
                <span class="label">📅 Start Date:</span> {tour.get("start_date", "")}<br>
                <span class="label">📅 End Date:</span> {tour.get("end_date", "")}<br>
                <span class="label">💰 Price:</span> {tour.get("price_aud", "")}<br>
                {"<span class='badge' style='background:#ffebee; color:#c62828;'>Limited Availability</span>" if tour.get("limited_availability") else ""}
            </div>
            <br>
            <form method='post'>
                <input type='submit' value='💾 Save Changes (UI Only)' style='padding:6px 12px; font-weight:600; background:#1976d2; color:white; border:none; border-radius:6px;'/>
            </form>
        </div>
        """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 30px; margin-bottom: 10px;">
    <div style='text-align: center; font-size: 13px; color: #888; margin-top: 10px;'>
      SS IntelliGuide • Designed by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
