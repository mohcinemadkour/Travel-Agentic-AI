# agents/flights_agent.py

from agents.flight_api_agent import _city_to_iata, _ensure_flight_urls


def recommend_flights(state):
    """
    Sort flights by price if available. If price is missing or not numeric,
    treat it as very expensive so it goes to the bottom.
    Ensures every flight has a URL that directs to that specific flight (cache-hit path).
    """
    origin_iata = _city_to_iata(state.origin or "") or "XXX"
    dest_iata = _city_to_iata(state.destination or "") or "XXX"
    _ensure_flight_urls(state, origin_iata, dest_iata)

    flights = state.flights or []

    def price_value(f):
        price = f.get("price")
        try:
            if price is None:
                return 9_999_999.0  # treat missing price as very high
            return float(price)
        except (TypeError, ValueError):
            return 9_999_999.0

    flights_sorted = sorted(flights, key=price_value)
    # Keep only top 5 cheapest
    state.flights = flights_sorted[:5]
    return state