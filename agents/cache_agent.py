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
    if not conn:
        return None
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
    # Match on both the raw user input and IATA codes (user may type "JFK" or "New York")
    origin_upper = (state.origin or "").strip().upper()
    dest_upper = (state.destination or "").strip().upper()
    cur.execute(
        """
        SELECT
            airline,
            origin,
            destination,
            price,
            url
        FROM flights
        WHERE (UPPER(origin) = %s OR UPPER(origin) = %s)
          AND (UPPER(destination) = %s OR UPPER(destination) = %s)
        LIMIT 20
        """,
        (origin_upper, state.origin, dest_upper, state.destination),
    )
    flight_cols = [col[0] for col in cur.description]
    flight_rows = cur.fetchall()
    flights = [dict(zip(flight_cols, row)) for row in flight_rows]

    # Cache hit only if BOTH hotels and a reasonable number of flights exist
    if len(hotels) > 0 and len(flights) >= 3:
        state.accommodations = hotels
        state.flights = flights
        return state

    # Cache miss
    return None