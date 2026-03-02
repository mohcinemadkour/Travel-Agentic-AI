# agents/flight_api_agent.py

import os
import requests
from urllib.parse import quote_plus

# City/code → IATA mapping for API and URL building
CITY_TO_IATA = {
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Bangalore": "BLR",
    "Bali": "DPS",
    "Tokyo": "HND",
    "Singapore": "SIN",
    "New York": "JFK",
    "Delhi": "DEL",
    "Chennai": "MAA",
    "Hyderabad": "HYD",
    "Kolkata": "CCU",
    "Dubai": "DXB",
    "London": "LHR",
    "Paris": "CDG",
    "Hong Kong": "HKG",
    "Bangkok": "BKK",
    "Sydney": "SYD",
    "Los Angeles": "LAX",
    "San Francisco": "SFO",
    "Chicago": "ORD",
    "Toronto": "YYZ",
}


def _city_to_iata(city: str) -> str:
    """Convert city name or code to IATA airport code."""
    if not city:
        return ""
    city_clean = city.strip()
    # Already looks like IATA (3 letters)?
    if len(city_clean) == 3 and city_clean.isalpha():
        return city_clean.upper()
    return CITY_TO_IATA.get(city_clean, city_clean.upper()[:3])


def _google_flights_url(origin: str, dest: str, start: str | None, end: str | None) -> str:
    """
    Build a real Google Flights search URL for this route and dates.
    """
    q = f"Flights from {origin} to {dest}"
    if start:
        q += f" on {start}"
    return f"https://www.google.com/travel/flights?q={quote_plus(q)}"


def _normalize_airline(name: str) -> str:
    """Normalize airline name for matching (LLM vs API may differ)."""
    if not name:
        return ""
    return name.lower().strip().replace(" ", "").replace("-", "")


def _ensure_google_flights_urls(state, origin_iata: str, dest_iata: str) -> None:
    """Ensure every flight has a Google Flights URL for the route. Works for future dates."""
    flights = state.flights or []
    for f in flights:
        if not f.get("url") or "google.com/travel/flights" not in (f.get("url") or ""):
            o = (f.get("origin") or origin_iata).upper()
            d = (f.get("destination") or dest_iata).upper()
            f["url"] = _google_flights_url(o, d, state.start_date, state.end_date)
    state.flights = flights


def _is_passenger_airline(name: str) -> bool:
    """
    Filter out obvious cargo/freight/logistics airlines.
    """
    if not name:
        return False
    nl = name.lower()
    banned_substrings = [
        "cargo",
        "freight",
        "logistics",
        "courier",
        "express",
        "blue dart",
        "fedex",
        "ups",
        "dhl",
    ]
    return not any(b in nl for b in banned_substrings)


# Common airline IATA -> display name (Aviation Edge routes API returns IATA only)
AIRLINE_IATA_TO_NAME = {
    "6E": "IndiGo",
    "9W": "Jet Airways",
    "AI": "Air India",
    "G8": "Go First",
    "SG": "SpiceJet",
    "UK": "Vistara",
    "AK": "AirAsia",
    "SQ": "Singapore Airlines",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "LH": "Lufthansa",
    "BA": "British Airways",
    "AA": "American Airlines",
    "DL": "Delta",
    "UA": "United",
}


def _fetch_aviation_edge_routes(api_key: str, origin_iata: str, dest_iata: str) -> list[dict]:
    """
    Fetch airline routes from Aviation Edge API (https://aviation-edge.com/developers).
    Uses routes endpoint: departureIata + arrivalIata.
    """
    url = "https://aviation-edge.com/v2/public/routes"
    params = {"key": api_key, "departureIata": origin_iata, "arrivalIata": dest_iata}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        return []
    return data


def fetch_flights_from_api(state):
    """
    Use Aviation Edge API (https://aviation-edge.com/developers) to discover
    real flights on the route. Enriches LLM flights with airline data and
    Google Flights URLs for booking.
    """

    origin_iata = _city_to_iata(state.origin or "")
    dest_iata = _city_to_iata(state.destination or "")

    if not origin_iata or not dest_iata:
        print("[Warning] Missing origin/destination IATA codes.")
        _ensure_google_flights_urls(state, origin_iata or "XXX", dest_iata or "XXX")
        return state

    # Support both Aviation Edge (preferred) and legacy AviationStack env var
    api_key = os.getenv("AVIATION_EDGE_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        _ensure_google_flights_urls(state, origin_iata, dest_iata)
        return state

    api_url_map: dict[tuple[str, str, str], tuple[str, str]] = {}
    seen_airlines: set[str] = set()

    try:
        data = _fetch_aviation_edge_routes(api_key, origin_iata, dest_iata)

        for f in data:
            airline_iata = (f.get("airlineIata") or "").upper()
            if not airline_iata or airline_iata in seen_airlines:
                continue
            airline_name = AIRLINE_IATA_TO_NAME.get(airline_iata, airline_iata)
            if not _is_passenger_airline(airline_name):
                continue
            seen_airlines.add(airline_iata)

            url = _google_flights_url(origin_iata, dest_iata, state.start_date, state.end_date)
            key = (_normalize_airline(airline_name), origin_iata, dest_iata)
            api_url_map[key] = (url, airline_name)

        # ── SMART MERGE ──────────────────────────────────────────────
        if state.flights:
            # Enrich existing LLM flights with API-matched URLs
            enriched = []
            for f in state.flights:
                airline = (f.get("airline") or "").strip()
                origin = (f.get("origin") or origin_iata).upper()
                dest = (f.get("destination") or dest_iata).upper()

                url = None
                if airline:
                    an_llm = _normalize_airline(airline)
                    for (an, o, d), (u, _) in api_url_map.items():
                        if o == origin and d == dest and (an == an_llm or an in an_llm or an_llm in an):
                            url = u
                            break

                f["url"] = url or _google_flights_url(origin_iata, dest_iata, state.start_date, state.end_date)
                enriched.append(f)

            state.flights = enriched
        elif api_url_map:
            # LLM produced no flights; use API flights as fallback
            fallback_flights = []
            for (_, o, d), (url, airline_name) in api_url_map.items():
                fallback_flights.append(
                    {
                        "airline": airline_name,
                        "origin": o,
                        "destination": d,
                        "price": None,
                        "url": url,
                    }
                )
            state.flights = fallback_flights[:5]

    except Exception as e:
        print(f"[Info] Aviation Edge API: {e!r} (using Google Flights URLs)")

    # Always ensure every flight has a working Google Flights URL (API free tier is real-time only)
    _ensure_google_flights_urls(state, origin_iata, dest_iata)

    return state