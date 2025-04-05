import streamlit as st
import json
import os

# --- Load JSON data ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
            tours.append(data)
        elif isinstance(data, list):
            tours = data

# --- App Title ---
st.set_page_config(layout="wide")
st.markdown("## 🌍 APT Tours Viewer & Editor")

# --- Search Field ---
search_term = st.text_input("🔎 Search by trip name, code, region, or country").lower()

# --- Filter Tours ---
filtered_tours = [
    tour for tour in tours
    if search_term in tour["trip_name"].lower()
    or search_term in tour["trip_code"].lower()
    or search_term in tour["region"].lower()
    or search_term in tour["country"].lower()
]

# --- Tour Cards ---
for tour in filtered_tours:
    with st.expander(f"📌 {tour['trip_name']} ({tour['trip_code']})"):
        left, right = st.columns([2, 1])

        with left:
            st.markdown(f"**🌍 Region:** {tour.get('region', '')}")
            st.markdown(f"**📍 Country:** {tour.get('country', '')}")
            st.markdown(f"**🔗 Original URL:** [{tour.get('original_url', '')}]({tour.get('original_url', '')})")
            st.markdown(f"**🔗 Booking URL:** [{tour.get('booking_url', '')}]({tour.get('booking_url', '')})")

            st.markdown("**📋 Trip Inclusions:**")
            st.markdown("\n".join([f"- {item}" for item in tour.get("trip_inclusions", [])]))

        with right:
            tour["start_date"] = st.text_input("📅 Start Date", value=tour.get("start_date", ""))
            tour["end_date"] = st.text_input("📅 End Date", value=tour.get("end_date", ""))
            tour["price_aud"] = st.text_input("💰 Price (AUD)", value=tour.get("price_aud", ""))
            tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False))

        if st.button("💾 Save Changes", key=tour["trip_code"]):
            with open(json_file, "w") as f:
                json.dump(tours, f, indent=2)
            st.success("✅ Tour info updated!")
