"""
Test: show generated flights from New York to DFW for 2026-03-03 to 2026-03-04.
Run: python tests/test_flights_newyork_dfw.py
     (set DUFFEL_API_KEY or AVIATION_EDGE_API_KEY in .env for live results)
"""

import sys
from pathlib import Path

# Ensure project root is on path and load .env
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))
try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

from state import TravelState
from agents.flight_api_agent import fetch_flights_from_api
from agents.flights_agent import recommend_flights


def test_show_flights_new_york_to_dfw():
    """Generate and print flights from New York to DFW, 2026-03-03 to 2026-03-04."""
    state = TravelState(
        origin="New York",
        destination="DFW",
        start_date="2026-03-03",
        end_date="2026-03-04",
    )
    state = fetch_flights_from_api(state)
    state = recommend_flights(state)

    flights = state.flights or []
    print("\n--- Generated flights: New York -> DFW (2026-03-03 to 2026-03-04) ---\n")
    if not flights:
        print("No flights returned (check DUFFEL_API_KEY / AVIATION_EDGE_API_KEY if needed).\n")
        return

    for i, f in enumerate(flights, 1):
        airline = f.get("airline") or "—"
        origin = f.get("origin") or "—"
        dest = f.get("destination") or "—"
        price = f.get("price")
        currency = f.get("total_currency") or "USD"
        price_str = f"{currency} {price:.0f}" if price is not None else "—"
        url = (f.get("url") or "").strip()
        print(f"{i}. {airline}  {origin} -> {dest}  {price_str}")
        if url:
            print(f"   Book: {url}")
        print()
    print("--- end ---\n")


if __name__ == "__main__":
    test_show_flights_new_york_to_dfw()
