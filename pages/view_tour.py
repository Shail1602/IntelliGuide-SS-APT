import streamlit as st
import json
import os
import math

# --- Page config ---
st.set_page_config(page_title="SS IntelliGuide – Tour Editor", layout="wide", page_icon="🌏")

# --- CSS Styling ---
st.markdown("""
<style>
    .header-banner {
        background: linear-gradient(90deg, #0077b6, #90e0ef);
        padding: 30px 40px;
        border-radius: 15px;
        margin-bottom: 30px;
        color: white;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        animation: fadein 1s ease;
    }

    .tour-card {
        background-color: #ffffff;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        padding: 24px;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        transition: all 0.25s ease-in-out;
        animation: fadein 0.6s ease;
        position: relative;
    }

    .tour-card:hover {
        box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    }

    .badge, .highlight {
        display: inline-block;
        border-radius: 9999px;
        font-size: 12px;
        padding: 4px 12px;
        margin: 2px 6px 2px 0;
    }

    .badge {
        background-color: #e0f2fe;
        color: #0369a1;
    }

    .highlight {
        background-color: #d1fae5;
        color: #065f46;
    }

    .ribbon {
        position: absolute;
        top: -10px;
        right: -10px;
        background-color: #ef4444;
        color: white;
        font-size: 10px;
        padding: 5px 10px;
        border-radius: 4px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }

    .ribbon.limited { background-color: #dc2626; }
    .ribbon.new { background-color: #10b981; }

    @keyframes fadein {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
</style>
""", unsafe_allow_html=True)

# --- Header Banner ---
st.markdown("""
<div class="header-banner">
    <h3>🌏 SS IntelliGuide – APT Tour Admin</h3>
    <p>Manage, Search & Edit Tours – backed by AI & Travel Intelligence</p>
</div>
""", unsafe_allow_html=True)

# --- Load JSON ---
json_file = "scraper/tour_info.json"
tours = []
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        tours = data if isinstance(data, list) else [data]

# --- Search, Sort & Pagination Controls ---
col1, col2, col3 = st.columns([4, 2, 1])
with col1:
    search_term = st.text_input("🔍 Search by name, code, region, or country").lower()
with col2:
    sort_by = st.selectbox("Sort by", ["None", "Region", "Country"])
with col3:
    total_pages = math.ceil(len(tours) / 15)
    page = st.number_input("📄 Page", min_value=1, max_value=max(1, total_pages), step=1)

# --- Filtering ---
filtered = [
    t for t in tours if search_term in t.get("trip_name", "").lower()
    or search_term in t.get("trip_code", "").lower()
    or search_term in t.get("region", "").lower()
    or search_term in t.get("country", "").lower()
]

if sort_by == "Region":
    filtered.sort(key=lambda x: x.get("region", ""))
elif sort_by == "Country":
    filtered.sort(key=lambda x: x.get("country", ""))

start_index = (page - 1) * 15
end_index = start_index + 15
paged = filtered[start_index:end_index]

# --- Highlights extraction ---
def get_highlights(inclusions):
    tags = []
    if not inclusions:
        return tags
    keywords = ["experience", "meal", "cruise", "tipping", "hand-picked", "local", "guide"]
    for inc in inclusions:
        for word in keywords:
            if word in inc.lower():
                tags.append(inc[:60] + "..." if len(inc) > 60 else inc)
                break
    return tags[:4]

# --- Cards per row ---
for i in range(0, len(paged), 3):
    row = st.columns(3)
    for j, tour in enumerate(paged[i:i+3]):
        with row[j]:
            is_unavailable = not any([tour.get("start_date"), tour.get("end_date"), tour.get("price_aud")])
            editable = st.checkbox("✏️ Edit", key=f"edit_{tour['trip_code']}")

            st.markdown("<div class='tour-card'>", unsafe_allow_html=True)

            # Ribbons
            if tour.get("limited_availability"):
                st.markdown("<div class='ribbon limited'>Limited</div>", unsafe_allow_html=True)
            elif "2025" in tour.get("booking_url", ""):
                st.markdown("<div class='ribbon new'>New</div>", unsafe_allow_html=True)

            # Title
            st.markdown(f"### 📌 {tour.get('trip_name', 'Untitled')} ({tour.get('trip_code', 'N/A')})", unsafe_allow_html=True)

            # Badges
            badges = ""
            if tour.get("region"): badges += f"<span class='badge'>{tour['region']}</span>"
            if tour.get("country"): badges += f"<span class='badge'>{tour['country']}</span>"
            st.markdown(badges, unsafe_allow_html=True)

            # Links
            st.markdown(f"🔗 <b>Original:</b> [{tour.get('original_url')}]({tour.get('original_url')})", unsafe_allow_html=True)

            if tour.get("booking_url"):
                st.markdown(f"🔗 <b>Booking:</b> [{tour['booking_url']}]({tour['booking_url']})", unsafe_allow_html=True)
                if is_unavailable:
                    st.info("🚫 Latest tour is not available.")
            else:
                st.warning("ℹ️ Request a quote by visiting the original tour page.")

            # Highlights
            highlights = get_highlights(tour.get("trip_inclusions", []))
            if highlights:
                st.markdown("🌟 <b>Highlights:</b>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='highlight'>{h}</span>" for h in highlights]), unsafe_allow_html=True)

            # Tour Details
            if not is_unavailable and editable:
                st.markdown("📁 **Tour Details**")
                tour["start_date"] = st.text_input("Start Date", value=tour.get("start_date", ""), key=f"start_{tour['trip_code']}")
                tour["end_date"] = st.text_input("End Date", value=tour.get("end_date", ""), key=f"end_{tour['trip_code']}")
                tour["price_aud"] = st.text_input("Price (AUD)", value=tour.get("price_aud", ""), key=f"price_{tour['trip_code']}")
                tour["limited_availability"] = st.checkbox("🔴 Limited Availability", value=tour.get("limited_availability", False), key=f"limit_{tour['trip_code']}")

                if st.button("💾 Save Changes", key=f"save_{tour['trip_code']}"):
                    with open(json_file, "w") as f:
                        json.dump(tours, f, indent=2)
                    st.success("✅ Tour info updated!")

            st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""---  
<div style='text-align: center; font-size: 13px; color: #999;'>SS IntelliGuide • Designed by Shailesh & Saumya</div>
""", unsafe_allow_html=True)
