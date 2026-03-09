import os
import traceback
from urllib.parse import quote_plus

from dotenv import load_dotenv
load_dotenv()

import requests
import streamlit as st

API_BASE = os.getenv("TRAVELTWIN_API_URL", "http://localhost:8000/api/v1")

ASSISTANT_AVATAR = "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=travel&backgroundColor=1e3a5f"

def _inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp { font-family: 'Inter', sans-serif; }

    /* ── Hero header ─────────────────────────────── */
    .hero {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    .hero h1 { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
    .hero p  { margin: 0.4rem 0 0 0; opacity: 0.8; font-size: 0.95rem; }

    /* ── Section headers ─────────────────────────── */
    .section-hdr {
        display: flex; align-items: center; gap: 0.5rem;
        margin: 1.8rem 0 0.8rem 0; padding-bottom: 0.4rem;
        border-bottom: 2px solid #e0e0e0;
    }
    .section-hdr .icon { font-size: 1.4rem; }
    .section-hdr .title { font-size: 1.15rem; font-weight: 600; color: #1a1a2e; }

    /* ── Weather card ────────────────────────────── */
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; padding: 1.2rem 1.5rem;
        color: white; font-size: 0.95rem; line-height: 1.6;
        margin-bottom: 0.5rem;
    }

    /* ── Hotel card ───────────────────────────────── */
    .hotel-card {
        background: #ffffff;
        border: 1px solid #e8ecf1;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .hotel-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    .hotel-rank {
        display: inline-block;
        background: linear-gradient(135deg, #0f2027, #2c5364);
        color: white;
        width: 28px; height: 28px; line-height: 28px;
        text-align: center; border-radius: 50%;
        font-size: 0.8rem; font-weight: 600;
        margin-right: 0.6rem; vertical-align: middle;
    }
    .hotel-name { font-weight: 600; font-size: 1.05rem; color: #1a1a2e; vertical-align: middle; }
    .hotel-meta { margin-top: 0.4rem; font-size: 0.85rem; color: #555; }
    .hotel-meta .stars { color: #f5a623; }
    .hotel-price {
        display: inline-block; background: #e8f5e9; color: #2e7d32;
        padding: 2px 10px; border-radius: 20px;
        font-weight: 600; font-size: 0.85rem; margin-left: 0.5rem;
    }
    .hotel-actions { margin-top: 0.5rem; font-size: 0.85rem; }
    .hotel-actions a {
        text-decoration: none; padding: 4px 14px; border-radius: 20px;
        font-weight: 500; margin-right: 0.5rem; display: inline-block;
    }
    .hotel-actions .map-btn { background: #e3f2fd; color: #1565c0; }
    .hotel-actions .map-btn:hover { background: #bbdefb; }
    .hotel-actions .book-btn { background: #1565c0; color: white; }
    .hotel-actions .book-btn:hover { background: #0d47a1; }

    /* ── Sidebar styling ─────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2027 0%, #203a43 100%);
    }
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stSlider label {
        color: #b0bec5 !important; font-weight: 500;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
        background: #ffffff !important;
        color: #1a1a2e !important;
        border: 1px solid #546e7a !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="input"] {
        background: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
        background: #ffffff !important;
    }
    [data-testid="stSidebar"] .stNumberInput input {
        background: #ffffff !important;
        color: #1a1a2e !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5 {
        color: #e0e0e0 !important;
    }

    /* ── Assistant bubble ─────────────────────────── */
    .assistant-msg {
        background: #f0f4f8; border-radius: 12px;
        padding: 1rem 1.2rem; margin: 0.8rem 0;
        border-left: 4px solid #1565c0;
        font-size: 0.92rem; color: #333; line-height: 1.5;
    }

    /* ── Misc ─────────────────────────────────────── */
    .empty-state { text-align: center; padding: 2rem; color: #999; font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)


def _stars_html(rating):
    try:
        r = float(rating)
    except (TypeError, ValueError):
        return ""
    full = int(r)
    half = 1 if r - full >= 0.3 else 0
    return '<span class="stars">' + ("★" * full) + ("½" * half) + "</span>" + f" {r:.1f}"


def run_workflow(origin, destination, start_date, end_date, bedrooms, max_price, min_rating):
    """Call the FastAPI /search endpoint."""
    resp = requests.post(
        f"{API_BASE}/search",
        json={
            "origin": origin,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "bedrooms": bedrooms,
            "max_price_per_night": max_price,
            "min_rating": min_rating,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _build_hotel_html(rank, h, destination):
    name = h.get("name") or "—"
    rating = h.get("rating")
    price = h.get("price") or h.get("price_per_night")
    photo = h.get("photo_url") or ""
    url = (h.get("url") or "").strip()
    map_url = (h.get("map_url") or "").strip()
    if not url or not url.startswith("http"):
        q = " ".join(filter(None, [name, h.get("city") or destination, "book"]))
        url = f"https://www.google.com/search?q={quote_plus(q)}"
    if not map_url or not map_url.startswith("http"):
        q = " ".join(filter(None, [name, h.get("city") or destination]))
        map_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"

    stars = _stars_html(rating)
    price_html = f'<span class="hotel-price">${price:.0f}/night</span>' if price else ""
    photo_html = f'<img src="{photo}" style="width:100%;border-radius:8px;margin-bottom:0.5rem;" />' if photo else ""

    return f"""
    <div class="hotel-card">
        {photo_html}
        <div>
            <span class="hotel-rank">{rank}</span>
            <span class="hotel-name">{name}</span>
        </div>
        <div class="hotel-meta">{stars} {price_html}</div>
        <div class="hotel-actions">
            <a class="map-btn" href="{map_url}" target="_blank">View on map</a>
            <a class="book-btn" href="{url}" target="_blank">Book now</a>
        </div>
    </div>
    """


def main():
    st.set_page_config(
        page_title="TravelTwin - AI Travel Assistant",
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1rem 0 0.5rem 0;">
            <img src="{ASSISTANT_AVATAR}" width="64" style="border-radius:50%;border:2px solid #4fc3f7;" />
            <h2 style="margin:0.4rem 0 0.1rem 0;font-size:1.2rem;color:white !important;">TravelTwin</h2>
            <p style="font-size:0.8rem;color:#90caf9 !important;margin:0;">Your AI Travel Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        with st.form("travel_form"):
            st.markdown("##### Plan your trip")
            origin = st.text_input("From", placeholder="e.g. JFK, SFO, London")
            destination = st.text_input("To", placeholder="e.g. MCO, Paris, Tokyo")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_date = st.date_input("Check-in")
            with col_d2:
                end_date = st.date_input("Check-out")
            bedrooms = st.number_input("Rooms", min_value=1, value=1)
            max_price = st.number_input("Max hotel $/night", min_value=0.0, value=200.0, step=10.0)
            min_rating = st.slider("Min rating", 0.0, 5.0, 4.0, 0.1)
            submitted = st.form_submit_button("Search", use_container_width=True)

    st.markdown("""
    <div class="hero">
        <h1>TravelTwin</h1>
        <p>Your AI-powered digital twin for finding the best hotels.</p>
    </div>
    """, unsafe_allow_html=True)

    if submitted:
        if not origin or not destination:
            st.error("Please provide both origin and destination.")
            return
        try:
            sd = start_date.isoformat()
            ed = end_date.isoformat()
        except Exception:
            sd, ed = str(start_date), str(end_date)

        try:
            with st.spinner("TravelTwin is searching for the best deals..."):
                final_state = run_workflow(origin, destination, sd, ed, int(bedrooms), float(max_price), float(min_rating))
            if not final_state:
                st.warning("No results found.")
                return
            st.session_state["travel_results"] = final_state
        except Exception as e:
            st.error(f"Workflow error: {e}")
            st.exception(traceback.format_exc())
            return

    final_state = st.session_state.get("travel_results")

    if not final_state:
        st.markdown("""
        <div class="assistant-msg">
            Welcome! I'm <strong>TravelTwin</strong>, your personal travel assistant.
            Fill in your trip details in the sidebar and click <strong>Search</strong>
            to find the best hotels for your trip.
        </div>
        """, unsafe_allow_html=True)
        return

    weather = final_state.get("weather_summary")
    hotels = final_state.get("recommended_hotels", [])
    dest = final_state.get("destination", "")
    orig = final_state.get("origin", "")

    st.markdown(f"""
    <div class="assistant-msg">
        Here are the best options I found for <strong>{orig}</strong> &rarr; <strong>{dest}</strong>
        ({final_state.get('start_date', '')} to {final_state.get('end_date', '')}).
    </div>
    """, unsafe_allow_html=True)

    if weather:
        st.markdown('<div class="section-hdr"><span class="icon">🌤️</span><span class="title">Weather Forecast</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="weather-card">{weather}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr"><span class="icon">🏨</span><span class="title">Top Hotels</span></div>', unsafe_allow_html=True)
    if hotels:
        cols = st.columns(min(len(hotels), 3))
        for i, h in enumerate(hotels):
            with cols[i % 3]:
                st.markdown(_build_hotel_html(i + 1, h, dest), unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">No hotel recommendations found.</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
