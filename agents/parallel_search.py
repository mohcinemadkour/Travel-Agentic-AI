# agents/parallel_search.py
"""
Run hotel search and flight API fetch in parallel to reduce total latency.
"""

from concurrent.futures import ThreadPoolExecutor

from agents.search_agent import live_search
from agents.flight_api_agent import fetch_flights_from_api


def _normalize_airline(name: str) -> str:
    if not name:
        return ""
    return name.lower().strip().replace(" ", "").replace("-", "")


def _fill_flight_prices_from_llm(api_flights: list, llm_flights: list) -> None:
    """When API flights have no price, fill from LLM flights by matching airline + route."""
    if not llm_flights:
        return
    for f in api_flights:
        if f.get("price") is not None:
            continue
        o = (f.get("origin") or "").upper()
        d = (f.get("destination") or "").upper()
        an = _normalize_airline(f.get("airline") or "")
        for llm in llm_flights:
            if an != _normalize_airline(llm.get("airline") or ""):
                continue
            if (llm.get("origin") or "").upper() != o or (llm.get("destination") or "").upper() != d:
                continue
            price = llm.get("price")
            if price is not None:
                try:
                    f["price"] = float(price)
                    if llm.get("total_currency"):
                        f["total_currency"] = llm.get("total_currency")
                except (TypeError, ValueError):
                    pass
                break


def _fill_llm_price_column(api_flights: list, llm_flights: list) -> None:
    """Attach the LLM estimated price as a separate field for comparison."""
    if not llm_flights:
        return
    for f in api_flights:
        o = (f.get("origin") or "").upper()
        d = (f.get("destination") or "").upper()
        an = _normalize_airline(f.get("airline") or "")
        for llm in llm_flights:
            if an != _normalize_airline(llm.get("airline") or ""):
                continue
            if (llm.get("origin") or "").upper() != o or (llm.get("destination") or "").upper() != d:
                continue
            price = llm.get("price")
            if price is not None:
                try:
                    f["llm_price"] = float(price)
                except (TypeError, ValueError):
                    pass
                break


def parallel_search(state):
    """
    Run live_search (hotels + LLM flights) and fetch_flights_from_api (Duffel/Aviation Edge)
    in parallel. Prefer API flights when available; otherwise use LLM flights.
    When API flights have no price (e.g. Aviation Edge), fill from LLM estimates.
    """
    state_hotels = state.model_copy(deep=True)
    state_flights = state.model_copy(deep=True)
    state_flights.accommodations = []
    state_flights.flights = []

    def run_hotel_search():
        return live_search(state_hotels)

    def run_flight_api():
        return fetch_flights_from_api(state_flights)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_hotels = executor.submit(run_hotel_search)
        future_flights = executor.submit(run_flight_api)
        result_hotels = future_hotels.result()
        result_flights = future_flights.result()

    state.accommodations = result_hotels.accommodations or []
    llm_flights = result_hotels.flights or []
    if result_flights.flights:
        state.flights = result_flights.flights
        # Tag each flight with its API price source, and attach LLM estimate for comparison
        for f in state.flights:
            f["api_price"] = f.get("price")  # real price from FlightAPI/Duffel/etc.
        _fill_llm_price_column(state.flights, llm_flights)
        _fill_flight_prices_from_llm(state.flights, llm_flights)
    else:
        state.flights = llm_flights
        for f in state.flights:
            f["llm_price"] = f.get("price")
    return state
