# agents/cache_agent.py

from database.singlestore_client import get_conn


def cache_agent(state):
    """
    Cache agent for the LangGraph travel app.

    - Checks SingleStore for cached accommodations for the given destination.
    - If hotels exist, returns an updated state (cache hit).
    - If not, returns None (cache miss), so the graph can route to the live_search node.
    """
    conn = get_conn()
    if not conn:
        return None
    cur = conn.cursor()

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

    if len(hotels) > 0:
        state.accommodations = hotels
        return state

    return None
