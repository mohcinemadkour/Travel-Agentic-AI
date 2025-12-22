from langgraph.graph import StateGraph, END

from state import TravelState
from agents.weather_agent import fetch_weather
from agents.search_agent import live_search
from agents.recommend_agent import recommend_hotels
from agents.flights_agent import recommend_flights
from agents.flight_api_agent import fetch_flights_from_api
from database.cache import check_cache
from database.store_results import store_results


def route_cache(state):
    if state is None:
        return "live_search"

    if isinstance(state, dict):
        accommodations = state.get("accommodations") or []
        flights = state.get("flights") or []
    else:
        accommodations = getattr(state, "accommodations", []) or []
        flights = getattr(state, "flights", []) or []

    if accommodations and flights:
        return "recommend_hotels"
    return "live_search"


def build_graph():
    graph = StateGraph(TravelState)

    graph.add_node("weather", fetch_weather)
    graph.add_node("cache", check_cache)
    graph.add_node("live_search", live_search)
    graph.add_node("flight_api", fetch_flights_from_api)
    graph.add_node("store", store_results)
    graph.add_node("recommend_hotels", recommend_hotels)
    graph.add_node("recommend_flights", recommend_flights)

    graph.set_entry_point("weather")

    graph.add_edge("weather", "cache")

    graph.add_conditional_edges(
        "cache",
        route_cache,
        {
            "live_search": "live_search",
            "recommend_hotels": "recommend_hotels",
        },
    )

    # Cache miss path: LLM → Flight API enrich → Store → Recommend
    graph.add_edge("live_search", "flight_api")
    graph.add_edge("flight_api", "store")
    graph.add_edge("store", "recommend_hotels")

    graph.add_edge("recommend_hotels", "recommend_flights")
    graph.add_edge("recommend_flights", END)

    return graph.compile()