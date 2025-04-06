import streamlit as st
import json
import os

# --- Setup ---
st.set_page_config(layout="wide", page_title="APT Tour Library", page_icon="🌍")

# --- Banner Header ---
st.markdown("""
    <style>
        .banner {
            background: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e') no-repeat center center;
            background-size: cover;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            color: white;
        }
        .banner h1 {
            margin: 0;
            font-size: 34px;
            font-weight: 700;
        }
        .banner p {
            margin: 5px 0 0;
            font-size: 16px;
            font-weight: 300;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 3px 8px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .badge {
            display: inline-block;
            font-size: 12px;
            background: #e3f2fd;
            color: #1565c0;
            padding: 4px 10px;
            border-radius: 50px;
            margin-right: 6px;
        }
        .label {
            font-weight: 600;
            font-size: 13px;
            margin-top: 8px;
        }
        .divider {
            height: 1px;
            background-color: #eee;
            margin: 15px 0;
        }
        .save-btn {
            background: #1976d2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 10px;
        }
        ul li {
            margin-bottom: 4px;
        }
    </style>
    <div class='banner'>
        <h1>🌍 APT Tour Library</h1>
        <p>Manage, search & edit luxury tours — just a click away.</p>
    </div>
    <br>
""", unsafe_allow_html=True)

# --- Load Tour Data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search Bar ---
search_term = st.text_input("🔎 Search by name, region, or country").strip().lower()

filtered_tours = [
    t for t in tours
    if search_term in t.get("trip_name", "").lower()
    or search_term in t.get("trip_code", "").lower()
    or search_term in t.get("region", "").lower()
    or search_term in t.get("country", "").lower()
]

# --- Two-Column Card Layout ---
cols = st.columns(2)
# In your loop for each tour
for idx, tour in enumerate(filtered_tours):
    with cols[idx % 2]:
        html = f"""
        <div class="card">
            <h4>📌 {tour.get("trip_name", "")} <span style='color:#999;'>({tour.get("trip_code", "")})</span></h4>
            <div>
                <span class="badge">{tour.get("region", "").capitalize()}</span>
                <span class="badge">{tour.get("country", "").capitalize()}</span>
            </div>

            <div class="divider"></div>

            <div class="label">🌐 Original:</div>
            <a href="{tour.get("original_url", "#")}" target="_blank">{tour.get("original_url", "")}</a>

            <div class="label">🛒 Booking:</div>
            <a href="{tour.get("booking_url", "#")}" target="_blank">{tour.get("booking_url", "")}</a>

            <div class="divider"></div>

            <div class="label">📋 Key Inclusions:</div>
            <ul>
                {''.join(f"<li>{item}</li>" for item in tour.get("trip_inclusions", []) if item.lower() != "title")}
            </ul>

            <div class="divider"></div>

            <div class="label">📅 Start Date:</div> {tour.get("start_date", "N/A")}<br>
            <div class="label">📅 End Date:</div> {tour.get("end_date", "N/A")}<br>
            <div class="label">💰 Price:</div> {tour.get("price_aud", "N/A")}<br>
            {'<div class="label" style="color:#c62828;">🔴 Limited Availability</div>' if tour.get("limited_availability") else ''}

            <button class="save-btn">💾 Save Changes</button>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


# --- Footer ---
st.markdown("""
    <br>
    <hr style="margin-top: 30px; margin-bottom: 10px;">
    <div style='text-align: center; font-size: 13px; color: #888;'>
      SS IntelliGuide • Designed by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
