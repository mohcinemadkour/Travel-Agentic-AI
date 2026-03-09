from dotenv import load_dotenv
load_dotenv()

from graph import build_graph
from state import TravelState


def main():
    print("=== AI Travel Agent (LangGraph Edition) ===")

    origin = 'BLR'
    destination = "Mumbai"
    start_date = '2025-12-12'
    end_date = '2026-01-12'

    bedrooms = 1
    max_price = 200
    min_rating = 4

    graph = build_graph()

    initial_state = TravelState(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        bedrooms=bedrooms,
        max_price_per_night=max_price,
        min_rating=min_rating,
    )

    final_state = graph.invoke(initial_state)

    if isinstance(final_state, TravelState):
        final_state = final_state.model_dump()

    weather_summary = final_state.get("weather_summary")
    recommended_hotels = final_state.get("recommended_hotels", [])

    print("\n=== WEATHER ===")
    if weather_summary:
        print(weather_summary)
    else:
        print("No weather summary available.")

    print("\n=== TOP HOTELS ===")
    if recommended_hotels:
        for h in recommended_hotels:
            name = h.get("name")
            rating = h.get("rating")
            price = h.get("price") or h.get("price_per_night")
            url = h.get("url")

            try:
                price_str = f"{float(price):.2f}" if price is not None else "N/A"
            except Exception:
                price_str = "N/A"

            print(f"- {name} — rating {rating} — {price_str} per night -> {url}")
    else:
        print("No hotel recommendations found.")

    print("\nDone! Your LangGraph-powered travel planning run is complete.\n")


if __name__ == "__main__":
    main()
