import streamlit as st
import json
import os

# Load tours from file
DATA_FILE = "scraper/tour_info.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

tours = load_data()

st.title("🌍 APT Tours Viewer & Editor")

# Search functionality
search = st.text_input("🔎 Search by trip name, code, region, or country")

filtered_tours = [tour for tour in tours if search.lower() in json.dumps(tour).lower()]

for idx, tour in enumerate(filtered_tours):
    with st.expander(f"🧭 {tour.get('trip_name', 'Unknown Tour')} ({tour.get('trip_code', '')})"):
        st.write(f"**Region:** {tour.get('region', '')}")
        st.write(f"**Country:** {tour.get('country', '')}")
        st.write(f"**Original URL:** {tour.get('original_url', '')}")
        st.write(f"**Booking URL:** {tour.get('booking_url', '')}")
        st.write(f"**Trip Inclusions:**")
        st.markdown("<ul>" + "".join(f"<li>{item}</li>" for item in tour.get("trip_inclusions", [])) + "</ul>", unsafe_allow_html=True)

        # Editable fields
        tour["start_date"] = st.text_input("Start Date", tour.get("start_date", ""), key=f"start_{idx}")
        tour["end_date"] = st.text_input("End Date", tour.get("end_date", ""), key=f"end_{idx}")
        tour["price_aud"] = st.text_input("Price (AUD)", tour.get("price_aud", ""), key=f"price_{idx}")
        tour["limited_availability"] = st.checkbox("Limited Availability", tour.get("limited_availability", False), key=f"limited_{idx}")

if st.button("💾 Save Changes"):
    save_data(tours)
    st.success("✅ Data saved to tour_info.json")
