from .singlestore_client import get_conn

def store_results(state):
    """
    Store freshly fetched accommodations and flights into SingleStore.
    Called only on cache miss.
    """
    conn = get_conn()
    cur = conn.cursor()

    # Accommodations
    for h in state.accommodations:
        # Table uses `location_city` / `location_country` columns.
        cur.execute(
            """
            INSERT INTO accommodations
                (name, location_city, location_country, price_per_night, rating, url, bedrooms)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                h.get("name"),
                h.get("city") or h.get("location_city"),
                h.get("country") or h.get("location_country"),
                h.get("price") or h.get("price_per_night"),
                h.get("rating"),
                h.get("url"),
                h.get("bedrooms"),
            ),
        )

    # Flights
    for f in state.flights:
        cur.execute(
            """
            INSERT INTO flights
                (airline, origin, destination, price, url)
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                f.get("airline"),
                f.get("origin"),
                f.get("destination"),
                f.get("price"),
                f.get("url"),
            )
        )

    conn.commit()