import streamlit as st
import json
import os

# --- Page Config ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Cards", page_icon="🌏")

# --- CSS Styling ---
st.markdown("""
<style>
.tour-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 25px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.badge {
    display: inline-block;
    background: #e0f2fe;
    color: #0369a1;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    margin-right: 6px;
}
.tour-title {
    font-size: 17px;
    font-weight: bold;
    margin-bottom: 4px;
}
.trip-row {
    display: flex;
    gap: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
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

# --- Render Tours in 3 Columns ---
for i in range(0, len(filtered_tours), 3):
    cols = st.columns(3)
    for j, col in enumerate(cols):
        if i + j < len(filtered_tours):
            tour = filtered_tours[i + j]
            with col:
                st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='tour-title'>📌 {tour.get('trip_name', '')} ({tour.get('trip_code', '')})</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<span class='badge'>{tour.get('region', '')}</span>"
                    f"<span class='badge'>{tour.get('country', '')}</span>",
                    unsafe_allow_html=True
                )
                st.markdown(f"🔗 <b>Original:</b> <a href='{tour.get('original_url', '')}' target='_blank'>{tour.get('original_url', '')}</a>", unsafe_allow_html=True)
                if tour.get("booking_url"):
                    st.markdown(f"🔗 <b>Booking:</b> <a href='{tour.get('booking_url', '')}' target='_blank'>{tour.get('booking_url', '')}</a>", unsafe_allow_html=True)
                
                # Inclusions
                if tour.get("trip_inclusions"):
                    st.markdown("**📋 Inclusions:**")
                    for item in tour.get("trip_inclusions", []):
                        st.markdown(f"- {item}")

                # Inputs for Start, End, Price
                start_col, end_col, price_col = st.columns(3)
                with start_col:
                    tour["start_date"] = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
                with end_col:
                    tour["end_date"] = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
                with price_col:
                    tour["price_aud"] = st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")

                tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")

                if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
                    with open(json_file, "w") as f:
                        json.dump(tours, f, indent=2)
                    st.success("✅ Tour updated!")
                st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("<hr style='margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 13px; color: #aaa;'>SS IntelliGuide • Built by Shailesh & Saumya</div>", unsafe_allow_html=True)
