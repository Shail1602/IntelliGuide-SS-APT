import streamlit as st
import json
import os

# --- App Config ---
st.set_page_config(page_title="APT Tour Library", layout="wide")

# --- Stylish Banner ---
st.markdown("""
    <div style="background: linear-gradient(to right, #0f766e, #2563eb);
                padding: 30px 40px;
                border-radius: 12px;
                color: white;
                margin-bottom: 20px;
                box-shadow: 0 3px 12px rgba(0,0,0,0.2);">
        <h2 style="margin-bottom: 6px;">🌊 APT Tour Library</h2>
        <p style="font-size: 14px; margin: 0;">Manage, search & edit luxury tours — just a click away.</p>
    </div>
""", unsafe_allow_html=True)

# --- Load JSON Data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search Box ---
search = st.text_input("🔍 Search by name, region, or country").lower()
filtered = [t for t in tours if search in t.get("trip_name", "").lower()
                                or search in t.get("region", "").lower()
                                or search in t.get("country", "").lower()]

# --- CSS Styling ---
st.markdown("""
<style>
.tour-card {
    background: white;
    border-radius: 12px;
    padding: 22px 26px;
    margin-bottom: 25px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    border-left: 5px solid #3b82f6;
}
.tour-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 5px;
}
.badge {
    display: inline-block;
    font-size: 11px;
    background: #e0f2fe;
    color: #0369a1;
    border-radius: 999px;
    padding: 3px 10px;
    margin-right: 5px;
    margin-top: 6px;
}
.label {
    font-weight: 600;
    margin-top: 12px;
}
.save-btn {
    background: #1d4ed8;
    color: white;
    padding: 7px 14px;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 12px;
    cursor: pointer;
}
.save-btn:hover {
    background: #1e40af;
}
</style>
""", unsafe_allow_html=True)

# --- Tour Cards in Two Columns ---
cols = st.columns(2)
for idx, tour in enumerate(filtered):
    with cols[idx % 2]:
        st.markdown(f"""
        <div class="tour-card">
            <div class="tour-title">📌 {tour.get("trip_name", "Untitled")} <span style='color:#666;'>({tour.get("trip_code", "")})</span></div>
            <div>
                <span class="badge">{tour.get("region", "").title()}</span>
                <span class="badge">{tour.get("country", "").title()}</span>
            </div>

            <div class="label">🌐 Original:</div>
            <a href="{tour.get("original_url", "#")}" target="_blank">{tour.get("original_url", "")}</a>

            <div class="label">🛒 Booking:</div>
            <a href="{tour.get("booking_url", "#")}" target="_blank">{tour.get("booking_url", "")}</a>

            <div class="label">📋 Key Inclusions:</div>
            <ul>
                {''.join([f"<li>{item}</li>" for item in tour.get("trip_inclusions", []) if item.lower() != "title"])}
            </ul>

            <div class="label">📅 Start Date:</div> {tour.get("start_date", "")}<br>
            <div class="label">📅 End Date:</div> {tour.get("end_date", "")}<br>
            <div class="label">💰 Price (AUD):</div> {tour.get("price_aud", "")}<br>
            {"<div class='label' style='color:#dc2626;'>🔴 Limited Availability</div>" if tour.get("limited_availability") else ""}
            
            <button class="save-btn">💾 Save Changes</button>
        </div>
        """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("<div style='text-align:center; font-size:13px; color:#999; margin-top:40px;'>SS IntelliGuide • Designed by Shailesh & Saumya</div>", unsafe_allow_html=True)
