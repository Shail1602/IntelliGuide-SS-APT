import streamlit as st
import json
import os
from datetime import datetime

# Load tours
TOUR_FILE = "scraper/tour_info.json"

def load_tours():
    if os.path.exists(TOUR_FILE):
        with open(TOUR_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]  # fallback if single object
    return []

def save_tours(tours):
    with open(TOUR_FILE, "w") as f:
        json.dump(tours, f, indent=2)

st.set_page_config(page_title="APT Tours Viewer & Editor", layout="wide")
st.title("🌍 APT Tours Viewer & Editor")

# Load tours
all_tours = load_tours()

# Search bar
search_query = st.text_input("🔍 Search by trip name, code, region, or country").lower()

# Filtered tours
filtered_tours = [tour for tour in all_tours if search_query in tour.get("trip_name", "").lower()
                  or search_query in tour.get("trip_code", "").lower()
                  or search_query in tour.get("region", "").lower()
                  or search_query in tour.get("country", "").lower()]

if not filtered_tours:
    st.info("No matching tours found. Try a different keyword.")

for idx, tour in enumerate(filtered_tours):
    with st.expander(f"🧳 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'No Code')})", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Region:** {tour.get('region', '')}")
            st.markdown(f"**Country:** {tour.get('country', '')}")
            st.markdown(f"**Original URL:** [{tour.get('original_url', '')}]({tour.get('original_url', '')})")
            st.markdown(f"**Booking URL:** [{tour.get('booking_url', '')}]({tour.get('booking_url', '')})")

            st.markdown("**Trip Inclusions:**")
            st.markdown("\n".join([f"- {item}" for item in tour.get("trip_inclusions", [])]))

        with col2:
            start_date = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{idx}")
            end_date = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{idx}")
            price = st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{idx}")
            limited = st.checkbox("Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{idx}")

            # Update object in memory
            tour["start_date"] = start_date
            tour["end_date"] = end_date
            tour["price_aud"] = price
            tour["limited_availability"] = limited

# Save all
if st.button("💾 Save Changes"):
    save_tours(all_tours)
    st.success("Tours updated successfully ✅")
