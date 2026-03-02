from langgraph.graph import StateGraph, END

from state import TravelState
from agents.init_parallel import init_parallel
from agents.parallel_search import parallel_search
from agents.recommend_agent import recommend_hotels
from agents.flights_agent import recommend_flights
from database.store_results import store_results


def route_cache(state):
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

    graph.add_node("init", init_parallel)
    graph.add_node("parallel_search", parallel_search)
    graph.add_node("store", store_results)
    graph.add_node("recommend_hotels", recommend_hotels)
    graph.add_node("recommend_flights", recommend_flights)

    graph.set_entry_point("init")

    graph.add_conditional_edges(
        "init",
        route_cache,
        {
            "live_search": "parallel_search",
            "recommend_hotels": "recommend_hotels",
        },
    )

    # Cache miss path: parallel hotel + flight fetch → Store → Recommend
    graph.add_edge("parallel_search", "store")
    graph.add_edge("store", "recommend_hotels")

    graph.add_edge("recommend_hotels", "recommend_flights")
    graph.add_edge("recommend_flights", END)

    return graph.compile()