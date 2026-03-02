import traceback
from urllib.parse import quote_plus

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
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
                # Show hotels with photos when available (from Google Places)
                has_photos = any(h.get("photo_url") for h in recommended_hotels)
                if has_photos:
                    for i, h in enumerate(recommended_hotels, 1):
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            photo_url = h.get("photo_url")
                            if photo_url:
                                st.image(photo_url, width=120)
                            else:
                                st.write("")
                        with col_info:
                            rank = i  # 1 = top pick, 2, 3, 4, 5
                            name = h.get("name") or "—"
                            rating = h.get("rating")
                            price = h.get("price") or h.get("price_per_night")
                            url = (h.get("url") or "").strip()
                            map_url = (h.get("map_url") or "").strip()
                            if not url or not url.startswith("http"):
                                q = " ".join(filter(None, [name, h.get("city") or final_state.get("destination"), "book"]))
                                url = f"https://www.google.com/search?q={quote_plus(q)}"
                            if not map_url or not map_url.startswith("http"):
                                q = " ".join(filter(None, [name, h.get("city") or final_state.get("destination")]))
                                map_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"
                            st.markdown(f"**#{rank} {name}**")
                            st.caption(f"⭐ {rating}  ·  {f'${price:.0f}/night' if price else '—'}  ·  [View on map]({map_url})  |  [Book]({url})")
                        st.divider()
                    st.caption("Prices are estimates from Google; verify on booking sites.")
                else:
                    hotels_data = []
                    for i, h in enumerate(recommended_hotels, 1):
                        rank = i  # 1 = top pick, 2, 3, 4, 5
                        url = (h.get("url") or "").strip()
                        map_url = (h.get("map_url") or "").strip()
                        if not url or not url.startswith("http"):
                            q = " ".join(filter(None, [h.get("name"), h.get("city") or final_state.get("destination"), "book"]))
                            url = f"https://www.google.com/search?q={quote_plus(q)}"
                        if not map_url or not map_url.startswith("http"):
                            q = " ".join(filter(None, [h.get("name"), h.get("city") or final_state.get("destination")]))
                            map_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"
                        hotels_data.append({
                            "#": rank,
                            "name": h.get("name") or "—",
                            "rating": h.get("rating"),
                            "price": h.get("price") or h.get("price_per_night"),
                            "map": map_url,
                            "book": url,
                        })
                    hotels_df = pd.DataFrame(hotels_data)
                    st.caption("Prices are AI-generated estimates; verify on booking sites.")
                    st.dataframe(
                        hotels_df,
                        use_container_width=True,
                        column_config={
                            "map": st.column_config.LinkColumn("View on map", display_text="Map"),
                            "book": st.column_config.LinkColumn("Book", display_text="Book"),
                        },
                        hide_index=True,
                    )
            else:
                st.write("No hotel recommendations found.")

            st.subheader("Top Flights")
            if flights:
                flights_data = []
                for f in flights:
                    url = (f.get("url") or "").strip()
                    if not url or not url.startswith("http"):
                        o, d = (f.get("origin") or "XXX").upper()[:3], (f.get("destination") or "XXX").upper()[:3]
                        url = f"https://www.google.com/travel/flights/flights-from-{o.lower()}-to-{d.lower()}.html"
                    price = f.get("price")
                    currency = f.get("total_currency") or "USD"
                    try:
                        price_str = f"{currency} {float(price):.0f}" if price is not None else None
                    except (TypeError, ValueError):
                        price_str = price
                    flights_data.append({
                        "airline": f.get("airline"),
                        "origin": f.get("origin"),
                        "destination": f.get("destination"),
                        "price": price_str or price,
                        "url": url,
                    })

                flights_df = pd.DataFrame(flights_data)
                st.dataframe(
                    flights_df,
                    use_container_width=True,
                    height=300,
                    column_config={
                        "url": st.column_config.LinkColumn("Links", display_text="Search flights"),
                    },
                    hide_index=True,
                )
            else:
                st.write("No flight options found.")

        except Exception as e:
            st.error(f"Workflow error: {e}")
            st.exception(traceback.format_exc())


if __name__ == "__main__":
    main()
