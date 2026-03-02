# agents/parallel_search.py
"""
Run hotel search and flight API fetch in parallel to reduce total latency.
"""

from concurrent.futures import ThreadPoolExecutor

from agents.search_agent import live_search
from agents.flight_api_agent import fetch_flights_from_api


def parallel_search(state):
    """
    Run live_search (hotels + LLM flights) and fetch_flights_from_api (Duffel/Aviation Edge)
    in parallel. Prefer API flights when available; otherwise use LLM flights.
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
    # Prefer API flights when available; else use LLM flights from live_search
    if result_flights.flights:
        state.flights = result_flights.flights
    else:
        state.flights = result_hotels.flights or []
    return state
