import streamlit as st
import json
import os

# --- App Config & Branding Banner ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- Business Header Banner ---
st.markdown("""
<div style='background: linear-gradient(to right, #e0f7fa, #ffffff);
            padding: 25px 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-top: 0px;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            justify-content: space-between;'>

    <div style='display: flex; align-items: center; gap: 18px;'>
        <div style='
            font-size: 46px;
            line-height: 1;
            margin-right: 10px;'>🌏
        </div>
        <div style='line-height: 1.4;'>
            <div style='font-size: 22px; font-weight: 700; color: #1f77b4;'>
                SS IntelliGuide – APT Tour Admin
            </div>
            <div style='font-size: 14.5px; color: #444;'>
                Manage, Search & Edit Tours – backed by AI & Travel Intelligence
            </div>
        </div>
    </div>

    <div>
        <img src='https://raw.githubusercontent.com/Shail1602/Inellibot/main/dbr.jpg' 
             alt='DB Results' 
             style='height: 50px; border-radius: 8px; box-shadow: 0 0 6px rgba(0,0,0,0.1);'>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Load JSON Data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            tours.append(data)
        elif isinstance(data, list):
            tours = data

# --- Search Field ---
search_term = st.text_input("🔎 Search by trip name, code, region, or country").lower()

# --- Filter Tours ---
filtered_tours = [
    tour for tour in tours 
    if search_term in tour.get("trip_name", "").lower() \
    or search_term in tour.get("trip_code", "").lower() \
    or search_term in tour.get("region", "").lower() \
    or search_term in tour.get("country", "").lower()
]

# --- Tour Cards ---
for tour in filtered_tours:
    with st.expander(f"📌 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})", expanded=False):
        left, right = st.columns([2, 1])

        with left:
            st.markdown(f"**🌍 Region:** {tour.get('region', '')}")
            st.markdown(f"**📍 Country:** {tour.get('country', '')}")
            st.markdown(f"**🔗 Original URL:** [{tour.get('original_url', '')}]({tour.get('original_url', '')})")
            st.markdown(f"**🔗 Booking URL:** [{tour.get('booking_url', '')}]({tour.get('booking_url', '')})")

            if tour.get("trip_inclusions"):
                st.markdown("**📋 Trip Inclusions:**")
                st.markdown("\n".join([f"- {item}" for item in tour.get("trip_inclusions", [])]))

        with right:
            tour["start_date"] = st.text_input("📅 Start Date", value=tour.get("start_date", ""), key=f"start_{tour.get('trip_code', '')}")
            tour["end_date"] = st.text_input("📅 End Date", value=tour.get("end_date", ""), key=f"end_{tour.get('trip_code', '')}")
            tour["price_aud"] = st.text_input("💰 Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour.get('trip_code', '')}")
            tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour.get('trip_code', '')}")

        if st.button("💾 Save Changes", key=f"save_{tour.get('trip_code', '')}"):
            with open(json_file, "w") as f:
                json.dump(tours, f, indent=2)
            st.success("✅ Tour info updated!")

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 30px; margin-bottom: 10px;">
    <div style='text-align: center; font-size: 13px; color: #888; margin-top: 10px;'>
      SS IntelliGuide • Designed by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
