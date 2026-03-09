import os
from dotenv import load_dotenv
load_dotenv()

from graph import build_graph
from state import TravelState

def test():
    graph = build_graph()

    initial_state = TravelState(
        origin="BLR",
        destination="Mumbai",
        start_date="2026-03-01",
        end_date="2026-03-05",
        bedrooms=1,
        max_price_per_night=200.0,
        min_rating=4.0,
    )

    final_state = graph.invoke(initial_state)

    if isinstance(final_state, TravelState):
        final_state = final_state.model_dump()

    print("--- FINAL HOTELS ---")
    print(final_state.get("recommended_hotels"))

test()
