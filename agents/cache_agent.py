# agents/cache_agent.py

from database.singlestore_client import get_conn


def cache_agent(state):
    """
    Cache agent for the LangGraph travel app.

    - Checks SingleStore for cached accommodations & flights
      for the given origin/destination.
    - If BOTH exist, returns an updated state (cache hit).
    - If not, returns None (cache miss), so the graph can
      route to the live_search node.
    """
    conn = get_conn()
    cur = conn.cursor()

    # ---- Hotels for this destination ----
    cur.execute(
        """
        SELECT
            name,
            city,
            country,
            price_per_night,
            rating,
            url,
            bedrooms
        FROM accommodations
        WHERE LOWER(city) = LOWER(%s)
        LIMIT 10
        """,
        (state.destination,),
    )
    hotel_cols = [col[0] for col in cur.description]
    hotel_rows = cur.fetchall()
    hotels = [dict(zip(hotel_cols, row)) for row in hotel_rows]

    # ---- Flights for this origin + destination ----
    cur.execute(
        """
        SELECT
            airline,
            origin,
            destination,
            price,
            url
        FROM flights
        WHERE origin = %s AND destination = %s
        LIMIT 10
        """,
        (state.origin, state.destination),
    )
    flight_cols = [col[0] for col in cur.description]
    flight_rows = cur.fetchall()
    flights = [dict(zip(flight_cols, row)) for row in flight_rows]

    # Cache hit only if BOTH hotels and flights exist
    if len(hotels) > 0 and len(flights) > 0:
        state.accommodations = hotels
        state.flights = flights
        return state

    # Cache miss
    return None