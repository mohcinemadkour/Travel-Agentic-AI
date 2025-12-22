from .singlestore_client import get_conn

def check_cache(state):
    """
    Check SingleStore for cached hotels & flights for this route.
    If BOTH exist, it's a cache hit. Otherwise, return None (cache miss).

    If the DB connection is unavailable (e.g., network/DNS issues in deployment),
    return None to allow the workflow to continue without cached data.
    """
    conn = get_conn()
    if not conn:
        # Couldn't connect to DB — treat as cache miss
        return None

    cur = conn.cursor()

    # Hotels for destination
    # `accommodations` table stores city/country in `location_city` / `location_country`.
    cur.execute("""
        SELECT
            name,
            location_city AS city,
            location_country AS country,
            price_per_night,
            rating,
            url,
            bedrooms
        FROM accommodations
        WHERE LOWER(location_city) = LOWER(%s)
        LIMIT 10
    """, (state.destination,))
    hotel_cols = [col[0] for col in cur.description]
    hotel_rows = cur.fetchall()
    hotels = [dict(zip(hotel_cols, r)) for r in hotel_rows]

    # Flights for origin + destination
    cur.execute("""
        SELECT
            airline,
            origin,
            destination,
            price,
            url
        FROM flights
        WHERE origin = %s AND destination = %s
        LIMIT 10
    """, (state.origin, state.destination))
    flight_cols = [col[0] for col in cur.description]
    flight_rows = cur.fetchall()
    flights = [dict(zip(flight_cols, r)) for r in flight_rows]

    if len(hotels) > 0 and len(flights) > 0:
        state.accommodations = hotels
        state.flights = flights
        return state

    # Cache miss
    return None