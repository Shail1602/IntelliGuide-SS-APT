
import streamlit as st
import json
import os
import math

st.set_page_config(page_title="SS IntelliGuide – Tour Admin", layout="wide", page_icon="🌏")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = True

def apply_styles():
    mode = "dark" if st.session_state.dark_mode else "light"
    background = "#111" if mode == "dark" else "#fff"
    text = "#f1f1f1" if mode == "dark" else "#111"
    card_bg = "#1e1e2f" if mode == "dark" else "#ffffff"
    border_color = "#333" if mode == "dark" else "#e5e7eb"
    input_bg = "#2c2c3c" if mode == "dark" else "#f8fafc"
    input_text = "#fff" if mode == "dark" else "#111"
    badge_bg = "#264653" if mode == "dark" else "#e0f2fe"
    badge_text = "#90e0ef" if mode == "dark" else "#0369a1"
    highlight_bg = "#014f86" if mode == "dark" else "#d1fae5"
    highlight_text = "#fff" if mode == "dark" else "#065f46"

    st.markdown(f"""
        <style>
        body, .stApp {{
            background-color: {background};
            color: {text};
        }}
        .tour-card {{
            background-color: {card_bg};
            border-radius: 14px;
            border: 1px solid {border_color};
            padding: 24px;
            margin-bottom: 30px;
            box-shadow: 0 6px 14px rgba(0,0,0,0.3);
            animation: fadeIn 0.8s ease-in-out;
        }}
        .tour-card:hover {{
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }}
        input[type="text"], textarea, .stTextInput > div > div > input {{
            background-color: {input_bg} !important;
            color: {input_text} !important;
            border: 1px solid #444 !important;
        }}
        .stCheckbox > div {{
            color: {text};
        }}
        .stNumberInput label, .stTextInput label {{
            color: {text};
        }}
        .badge {{
            display: inline-block;
            background-color: {badge_bg};
            color: {badge_text};
            border-radius: 9999px;
            font-size: 12px;
            padding: 4px 12px;
            margin: 2px 5px 2px 0;
        }}
        .highlight {{
            background-color: {highlight_bg};
            color: {highlight_text};
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 999px;
            margin: 4px 5px 4px 0;
            display: inline-block;
        }}
        .stButton button {{
            background: linear-gradient(90deg, #00b4d8, #0077b6);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-weight: 600;
        }}
        .stButton button:hover {{
            background: linear-gradient(90deg, #0096c7, #005f73);
        }}
        @keyframes fadeIn {{
            0% {{ opacity: 0; transform: translateY(20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
    """, unsafe_allow_html=True)


apply_styles()

st.markdown("""
    <div style='background: linear-gradient(90deg, #0077b6, #90e0ef); padding: 25px 40px; border-radius: 15px; margin-bottom: 30px; color: white;'>
        <h2>🌏 SS IntelliGuide – APT Tour Admin</h2>
        <p>Manage, Search, Edit & Export Tours</p>
    </div>
""", unsafe_allow_html=True)

top_left, top_right = st.columns([5, 1])
with top_left:
    search = st.text_input("🔍 Search tours").lower()
with top_right:
    st.toggle("🌗 Dark Mode", key="dark_mode", on_change=apply_styles)
    st.toggle("✏️ Edit Mode", key="edit_mode")

json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        tours = json.load(f)

filtered = [t for t in tours if search in t.get("trip_name", "").lower() or
            search in t.get("trip_code", "").lower() or
            search in t.get("region", "").lower() or
            search in t.get("country", "").lower()]

total_pages = math.ceil(len(filtered) / 15)
page = st.number_input("📄 Page", min_value=1, max_value=max(1, total_pages), step=1)
paged = filtered[(page - 1) * 15 : (page * 15)]

def get_highlights(inclusions):
    tags = []
    if not inclusions: return tags
    keywords = ["experience", "meal", "cruise", "tipping", "hand-picked", "local", "guide"]
    for inc in inclusions:
        if any(word in inc.lower() for word in keywords):
            tags.append(inc[:60] + "..." if len(inc) > 60 else inc)
    return tags[:4]

for i in range(0, len(paged), 3):
    row = st.columns(3)
    for j, tour in enumerate(paged[i:i+3]):
        with row[j]:
            st.markdown("<div class='tour-card'>", unsafe_allow_html=True)
            st.markdown(f"### 📌 {tour.get('trip_name')} ({tour.get('trip_code')})", unsafe_allow_html=True)
            st.markdown("".join([
                f"<span class='badge'>{tour.get('region')}</span>",
                f"<span class='badge'>{tour.get('country')}</span>"
            ]), unsafe_allow_html=True)

            booking = tour.get("booking_url", "").strip()
            missing_details = not tour.get("start_date") or not tour.get("end_date")
            if not booking:
                st.warning("📩 Request a quote by visiting the tour page.")
            elif missing_details:
                st.info("ℹ️ Latest tour info is sold out or not available.")

            st.markdown(f"🔗 [Original Page]({tour.get('original_url')})", unsafe_allow_html=True)
            if booking:
                st.markdown(f"🔗 [Booking Page]({booking})", unsafe_allow_html=True)

            for tag in get_highlights(tour.get("trip_inclusions")):
                st.markdown(f"<span class='highlight'>{tag}</span>", unsafe_allow_html=True)

            if booking and not missing_details and st.session_state.edit_mode:
                tour["start_date"] = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
                tour["end_date"] = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
                tour["price_aud"] = st.text_input("Price AUD", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")
                tour["limited_availability"] = st.checkbox("Limited Availability", value=tour.get("limited_availability", False), key=f"avail_{tour['trip_code']}")
                if st.button("💾 Save", key=f"save_{tour['trip_code']}"):
                    with open(json_file, "w") as f:
                        json.dump(tours, f, indent=2)
                    st.success("✅ Updated")
            st.markdown("</div>", unsafe_allow_html=True)

with st.expander("📂 Export Data"):
    export_format = st.radio("Choose Format", ["JSON", "CSV"])
    if st.button("Export Now"):
        if export_format == "JSON":
            st.download_button("Download JSON", json.dumps(tours, indent=2), file_name="tours_export.json")
        else:
            import pandas as pd
            df = pd.DataFrame(tours)
            st.download_button("Download CSV", df.to_csv(index=False), file_name="tours_export.csv")

st.markdown("---")
st.markdown("<div style='text-align: center; font-size: 13px; color: gray;'>SS IntelliGuide - Designed by Shailesh and Saumya</div>", unsafe_allow_html=True)
