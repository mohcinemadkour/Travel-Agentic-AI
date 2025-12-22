import traceback
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from graph import build_graph
from state import TravelState


def run_workflow(origin, destination, start_date, end_date, bedrooms, max_price, min_rating):
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

    return final_state


def main():
    st.set_page_config(page_title="AI Travel Agent", layout="wide")
    st.title("🌍 AI Travel Agent (LangGraph Edition)")

    with st.form("travel_form"):
        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Origin (e.g., BLR)")
            start_date = st.date_input("Start date")
            bedrooms = st.number_input("Bedrooms", min_value=1, value=1)
            max_price = st.number_input("Max price per night", min_value=0.0, value=200.0, step=1.0)
        with col2:
            destination = st.text_input("Destination (e.g., Mumbai)")
            end_date = st.date_input("End date")
            min_rating = st.slider("Min rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)

        submitted = st.form_submit_button("Search")

    if submitted:
        if not origin or not destination:
            st.error("Please provide both origin and destination.")
            return

        # Convert dates to ISO strings
        try:
            sd = start_date.isoformat()
            ed = end_date.isoformat()
        except Exception:
            sd = str(start_date)
            ed = str(end_date)

        try:
            with st.spinner("Running agent workflow — this may take a while..."):
                final_state = run_workflow(origin, destination, sd, ed, int(bedrooms), float(max_price), float(min_rating))

            if not final_state:
                st.warning("Workflow returned no results.")
                return

            weather_summary = final_state.get("weather_summary")
            recommended_hotels = final_state.get("recommended_hotels", [])
            flights = final_state.get("flights", [])

            st.subheader("Weather")
            if weather_summary:
                st.write(weather_summary)
            else:
                st.write("No weather summary available.")

            st.subheader("Top Hotels")
            if recommended_hotels:
                st.table([{"name": h.get("name"), "rating": h.get("rating"), "price": (h.get("price") or h.get("price_per_night")), "url": h.get("url")} for h in recommended_hotels])
            else:
                st.write("No hotel recommendations found.")

            st.subheader("Top Flights")
            if flights:
                    flights_df = []
                    for f in flights:
                        dep = f.get("departure_time") or f.get("departure") or f.get("depart_time") or f.get("time")
                        arr = f.get("arrival_time") or f.get("arrival")
                        time_range = None
                        if dep and arr:
                            time_range = f"{dep} → {arr}"
                        elif dep:
                            time_range = dep
                        elif arr:
                            time_range = arr

                        flights_df.append({
                            "airline": f.get("airline"),
                            "origin": f.get("origin"),
                            "destination": f.get("destination"),
                            "time": time_range,
                            "price": f.get("price"),
                            "url": f.get("url"),
                        })

                    st.dataframe(flights_df, use_container_width=True, height=300)
            else:
                st.write("No flight options found.")

        except Exception as e:
            st.error(f"Workflow error: {e}")
            st.exception(traceback.format_exc())


if __name__ == "__main__":
    main()
