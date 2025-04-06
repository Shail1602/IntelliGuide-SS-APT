import streamlit as st
import json
import os

# --- Config ---
st.set_page_config(page_title="APT Tour Library", layout="wide")

# --- Banner Header ---
st.markdown("""
    <div style="background: linear-gradient(90deg, #005f73, #0a9396); 
                padding: 30px 25px; 
                border-radius: 14px; 
                margin-bottom: 25px;
                background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e');
                background-size: cover;
                background-position: center;
                color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
        <h2 style='margin-bottom: 8px;'>🌊 APT Tour Library</h2>
        <p style='margin: 0;'>Manage, search & edit luxury tours — just a click away.</p>
    </div>
""", unsafe_allow_html=True)

# --- Load JSON Data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search ---
search = st.text_input("🔍 Search by name, region, or country").lower()
filtered = [t for t in tours if search in t.get("trip_name", "").lower() 
                                or search in t.get("region", "").lower()
                                or search in t.get("country", "").lower()]

# --- CSS Styling ---
st.markdown("""
    <style>
        .tour-card {
            background: #fff;
            border-radius: 12px;
            padding: 20px 25px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 5px solid #3b82f6;
        }
        .tour-title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #1f2937;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            margin-right: 6px;
            margin-top: 6px;
            font-size: 11px;
            background: #e0f2fe;
            color: #0284c7;
            border-radius: 12px;
        }
        .label {
            font-weight: 600;
            margin-top: 10px;
            margin-bottom: 4px;
        }
        .save-btn {
            background: #1d4ed8;
            color: white;
            padding: 8px 18px;
            border-radius: 8px;
            margin-top: 10px;
            border: none;
            font-weight: 600;
            cursor: pointer;
        }
        .save-btn:hover {
            background: #1e40af;
        }
        .divider {
            margin: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }
    </style>
""", unsafe_allow_html=True)

# --- Display Cards ---
cols = st.columns(2)
for idx, tour in enumerate(filtered):
    with cols[idx % 2]:
        html_parts = []

        html_parts.append(f"""
        <div class="tour-card">
            <div class="tour-title">📌 {tour.get("trip_name", "")} <span style='color:#888;'>({tour.get("trip_code", "")})</span></div>
            <div>
                <span class="badge">{tour.get("region", "").title()}</span>
                <span class="badge">{tour.get("country", "").title()}</span>
            </div>
            <div class="divider"></div>

            <div class="label">🌐 Original:</div>
            <a href="{tour.get("original_url", "#")}" target="_blank">{tour.get("original_url", "")}</a>

            <div class="label">🛒 Booking:</div>
            <a href="{tour.get("booking_url", "#")}" target="_blank">{tour.get("booking_url", "")}</a>

            <div class="divider"></div>
            <div class="label">📋 Key Inclusions:</div>
            <ul>
        """)
        for item in tour.get("trip_inclusions", []):
            if item and item.lower() != "title":
                html_parts.append(f"<li>{item}</li>")

        html_parts.append("</ul><div class='divider'></div>")

        html_parts.append(f"""
            <div class="label">📅 Start Date:</div> {tour.get("start_date", "")}
            <div class="label">📅 End Date:</div> {tour.get("end_date", "")}
            <div class="label">💰 Price (AUD):</div> {tour.get("price_aud", "")}
        """)

        if tour.get("limited_availability"):
            html_parts.append("<div class='label' style='color:#dc2626;'>🔴 Limited Availability</div>")

        html_parts.append("<button class='save-btn'>💾 Save Changes</button></div>")

        st.markdown("\n".join(html_parts), unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <div style='text-align: center; font-size: 13px; color: #aaa; margin-top: 40px;'>
        SS IntelliGuide • Designed by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
