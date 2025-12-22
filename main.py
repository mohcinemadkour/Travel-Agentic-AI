from dotenv import load_dotenv
load_dotenv()

from graph import build_graph
from state import TravelState


def main():
    print("=== AI Travel Agent (LangGraph Edition) ===")

    # origin = input("Origin (e.g., BLR): ").strip()
    # destination = input("Destination (e.g., Mumbai): ").strip()
    # start_date = input("Start date (YYYY-MM-DD): ").strip()
    # end_date = input("End date (YYYY-MM-DD): ").strip()

    # bedrooms = int(input("Bedrooms (default 1): ") or 1)
    # max_price = float(input("Max price per night (default 200): ") or 200)
    # min_rating = float(input("Min rating (default 4.0): ") or 4.0)

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

    # Normalize to dict
    if isinstance(final_state, TravelState):
        final_state = final_state.model_dump()

    weather_summary = final_state.get("weather_summary")
    recommended_hotels = final_state.get("recommended_hotels", [])
    flights = final_state.get("flights", [])

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

            print(f"- {name} — ⭐ {rating} — {price_str} per night → {url}")
    else:
        print("No hotel recommendations found.")

    print("\n=== TOP FLIGHTS ===")
    if flights:
        for f in flights:
            airline = f.get("airline")
            origin_f = f.get("origin")
            dest_f = f.get("destination")
            price = f.get("price")
            url = f.get("url")
            # Support several possible time keys from different agents
            dep = f.get("departure_time") or f.get("departure") or f.get("depart_time") or f.get("time")
            arr = f.get("arrival_time") or f.get("arrival")
            if dep and arr:
                time_str = f" ({dep} → {arr})"
            elif dep:
                time_str = f" ({dep})"
            elif arr:
                time_str = f" ({arr})"
            else:
                time_str = ""

            print(f"- {airline} {origin_f} → {dest_f}{time_str} — {price} → {url}")
    else:
        print("No flight options found.")

    print("\n🎉 Done! Your LangGraph-powered travel planning run is complete.\n")


if __name__ == "__main__":
    main()