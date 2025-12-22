# agents/flights_agent.py

def recommend_flights(state):
    """
    Sort flights by price if available. If price is missing or not numeric,
    treat it as very expensive so it goes to the bottom.
    """

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