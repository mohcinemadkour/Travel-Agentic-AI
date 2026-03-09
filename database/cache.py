from .singlestore_client import get_conn

try:
    from agents.destination_utils import resolve_destination_for_hotels
except ImportError:
    def resolve_destination_for_hotels(x): return x or ""


def check_cache(state):
    """
    Check SingleStore for cached hotels for this destination.
    If hotels exist, it's a cache hit. Otherwise, return None (cache miss).

    If the DB connection is unavailable (e.g., network/DNS issues in deployment),
    return None to allow the workflow to continue without cached data.
    """
    conn = get_conn()
    if not conn:
        return None

    cur = conn.cursor()

    hotel_destination = resolve_destination_for_hotels(state.destination or "")

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
    """, (hotel_destination or state.destination,))
    hotel_cols = [col[0] for col in cur.description]
    hotel_rows = cur.fetchall()
    hotels = [dict(zip(hotel_cols, r)) for r in hotel_rows]

    if len(hotels) > 0:
        state.accommodations = hotels
        return state

    return None
