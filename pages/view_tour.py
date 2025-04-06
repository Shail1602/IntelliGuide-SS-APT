import streamlit as st
import json
import os

# --- App Config & Branding Banner ---
st.set_page_config(layout="wide", page_title="SS IntelliGuide – Tour Editor", page_icon="🌏")

# --- Business Header Banner ---
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("### 🌏 SS IntelliGuide – APT Tour Admin")
    st.markdown("##### Manage, Search & Edit Tours – backed by AI & Travel Intelligence")
with col2:
    st.image("https://raw.githubusercontent.com/Shail1602/Inellibot/main/dbr.jpg", width=60)

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
    if search_term in tour.get("trip_name", "").lower()
    or search_term in tour.get("trip_code", "").lower()
    or search_term in tour.get("region", "").lower()
    or search_term in tour.get("country", "").lower()
]

# --- Tour Cards with Editable Fields ---
for idx, tour in enumerate(filtered_tours):
    with st.container():
        st.markdown(f"""
            <div style="
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                padding: 20px 25px;
                margin-bottom: 20px;
                transition: box-shadow 0.3s ease-in-out;
            " onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'" onmouseout="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)'">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1; padding-right: 20px;">
                        <h4 style="margin-bottom: 5px;">📌 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})</h4>
                        <p style="margin: 0; font-size: 14px;"><strong>Region:</strong> {tour.get('region', '')} | <strong>Country:</strong> {tour.get('country', '')}</p>
                        <p style="margin: 5px 0;"><strong>🔗 Original:</strong> <a href="{tour.get('original_url', '')}" target="_blank">{tour.get('original_url', '')}</a></p>
                        <p style="margin: 5px 0;"><strong>🔗 Booking:</strong> <a href="{tour.get('booking_url', '')}" target="_blank">{tour.get('booking_url', '')}</a></p>
                        <p style="margin: 5px 0;"><strong>📋 Inclusions:</strong></p>
                        <ul style="margin-top: 5px;">
                            {''.join(f"<li>{inc}</li>" for inc in tour.get('trip_inclusions', [])[:5])}
                        </ul>
                    </div>
                    <div style="min-width: 260px;">
        """, unsafe_allow_html=True)

        # Right-side editable fields
        tour["start_date"] = st.text_input("📅 Start Date", value=tour.get("start_date", ""), key=f"start_{idx}")
        tour["end_date"] = st.text_input("📅 End Date", value=tour.get("end_date", ""), key=f"end_{idx}")
        tour["price_aud"] = st.text_input("💰 Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{idx}")
        tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{idx}")

        if st.button("💾 Save Changes", key=f"save_{idx}"):
            with open(json_file, "w") as f:
                json.dump(tours, f, indent=2)
            st.success("✅ Tour info updated!")

        st.markdown("</div></div></div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 30px; margin-bottom: 10px;">
    <div style='text-align: center; font-size: 13px; color: #888; margin-top: 10px;'>
      SS IntelliGuide • Designed by Shailesh & Saumya
    </div>
""", unsafe_allow_html=True)
