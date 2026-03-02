# agents/recommend_agent.py

from urllib.parse import quote_plus


def _hotel_search_url(name: str, city: str, country: str | None = None) -> str:
    """Build a search URL that surfaces booking sites (Booking.com, Expedia, etc.)."""
    parts = [name, city]
    if country:
        parts.append(country)
    parts.append("book")
    q = " ".join(p for p in parts if p)
    return f"https://www.google.com/search?q={quote_plus(q)}"


def recommend_hotels(state):
    """
    Sort accommodations by rating (desc), then price (asc),
    and pick top 5. Also replaces dummy URLs with real
    Google Search URLs for each hotel.
    """
    hotels = state.accommodations or []

    def score(h):
        rating = h.get("rating") or 0.0
        price = h.get("price") or h.get("price_per_night") or 0.0
        try:
            rating_f = float(rating)
        except Exception:
            rating_f = 0.0
        try:
            price_f = float(price)
        except Exception:
            price_f = 0.0
        # Higher rating, lower price
        return (-rating_f, price_f)

    hotels_sorted = sorted(hotels, key=score)
    top_hotels = hotels_sorted[:5]

    # Ensure each has a real, clickable URL (preserve Google Maps URL from Places API)
    for h in top_hotels:
        url = h.get("url") or ""
        if not url or "google.com/maps" not in url:
            name = h.get("name") or ""
            city = h.get("city") or state.destination
            country = h.get("country") or ""
            h["url"] = _hotel_search_url(name, city, country)

    state.recommended_hotels = top_hotels
    return state