import streamlit as st
import json
import os

st.set_page_config(page_title="APT Tour Library", layout="wide")

# ---- Header ----
st.markdown("""
    <div style="background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e');
        background-size: cover;
        background-position: center;
        padding: 32px 32px 50px 32px;
        border-radius: 18px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <h2 style='margin: 0;'>🌍 APT Tour Library</h2>
        <p style='font-size: 16px; margin-top: 6px;'>Manage, search & edit luxury tours — just a click away.</p>
    </div>
""", unsafe_allow_html=True)

# ---- Load JSON ----
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            tours.append(data)
        elif isinstance(data, list):
            tours = data

# ---- Search ----
search = st.text_input("🔍 Search by name, region, or country").lower()
filtered = [t for t in tours if search in t.get("trip_name", "").lower() 
                                or search in t.get("region", "").lower()
                                or search in t.get("country", "").lower()]

# ---- Styling ----
st.markdown("""
    <style>
        .tour-card {
            background: #fff;
            border-radius: 12px;
            padding: 20px 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            border-left: 5px solid #1f77b4;
        }
        .tour-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #333;
        }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            margin-right: 6px;
            margin-top: 4px;
            font-size: 11px;
            background: #e0f3ff;
            color: #0077b6;
            border-radius: 10px;
        }
        .label {
            font-weight: 600;
            margin-top: 10px;
            margin-bottom: 4px;
        }
        .divider {
            margin: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .save-btn {
            background: #1f77b4;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            margin-top: 8px;
            border: none;
            font-weight: 600;
            cursor: pointer;
        }
        .save-btn:hover {
            background: #125a8a;
        }
    </style>
""", unsafe_allow_html=True)

# ---- Display Cards ----
cols = st.columns(2)
for idx, tour in enumerate(filtered):
    with cols[idx % 2]:
        html = f"""
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
                {''.join(f"<li>{item}</li>" for item in tour.get("trip_inclusions", []) if item and item.lower() != "title")}
            </ul>

            <div class="divider"></div>

            <div class="label">📅 Start Date:</div> {tour.get("start_date", "")}
            <div class="label">📅 End Date:</div> {tour.get("end_date", "")}
            <div class="label">💰 Price (AUD):</div> {tour.get("price_aud", "")}
            { '<div class="label" style="color:#c62828;">🔴 Limited Availability</div>' if tour.get("limited_availability") else '' }

            <button class="save-btn">💾 Save Changes</button>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

# ---- Footer ----
st.markdown("""
    <div style='text-align:center; font-size: 12px; color: #aaa; margin-top: 40px;'>
    SS IntelliGuide • Built by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
