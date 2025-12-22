# agents/flight_api_agent.py

import os
import requests
from urllib.parse import quote_plus

# Minimal city → IATA mapping for demo
CITY_TO_IATA = {
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Bangalore": "BLR",
    "Bali": "DPS",
    "Tokyo": "HND",
    "Singapore": "SIN",
    "New York": "JFK",
}


def _city_to_iata(city: str) -> str:
    if not city:
        return ""
    city_clean = city.strip()
    return CITY_TO_IATA.get(city_clean, city_clean.upper()[:3])


def _google_flights_url(origin: str, dest: str, start: str | None, end: str | None) -> str:
    """
    Build a real Google Flights search URL for this route and dates.
    """
    q = f"Flights from {origin} to {dest}"
    if start:
        q += f" on {start}"
    return f"https://www.google.com/travel/flights?q={quote_plus(q)}"


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


def fetch_flights_from_api(state):
    """
    SMART MERGE (Option C):

    - Keep LLM-generated flights (with good prices).
    - Use AviationStack only to:
        * discover real passenger airlines on this route
        * generate real Google Flights URLs
    - If LLM flights exist:
        * Enrich their URLs using Google Flights links from API
        * Keep LLM prices as-is
    - If LLM flights are empty:
        * Use API flights as fallback (price=None).
    """

    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        print("⚠️ AVIATIONSTACK_API_KEY not set; skipping real flight API.")
        return state

    origin_iata = (state.origin or "").upper()
    dest_iata = _city_to_iata(state.destination)

    if not origin_iata or not dest_iata:
        print("⚠️ Missing origin/destination IATA codes, cannot query AviationStack.")
        return state

    params = {
        "access_key": api_key,
        "dep_iata": origin_iata,
        "arr_iata": dest_iata,
        "limit": 20,
    }

    try:
        resp = requests.get("http://api.aviationstack.com/v1/flights", params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", []) or []

        # Build map: (airline_lower, origin, dest) -> google_flights_url
        api_url_map: dict[tuple[str, str, str], str] = {}

        for f in data:
            airline_info = f.get("airline") or {}
            airline_name = airline_info.get("name") or ""
            if not _is_passenger_airline(airline_name):
                continue

            # We ignore times and just build a generic Google Flights URL
            url = _google_flights_url(origin_iata, dest_iata, state.start_date, state.end_date)

            key = (airline_name.lower(), origin_iata, dest_iata)
            # Last one wins; that's fine
            api_url_map[key] = url

        if not api_url_map:
            print("⚠️ AviationStack returned no suitable passenger flights; leaving flights unchanged.")
            return state

        # ── SMART MERGE ──────────────────────────────────────────────
        if state.flights:
            # Enrich existing LLM flights
            enriched = []
            for f in state.flights:
                airline = (f.get("airline") or "").strip()
                if not airline:
                    enriched.append(f)
                    continue

                # Normalize route
                origin = (f.get("origin") or origin_iata).upper()
                dest = (f.get("destination") or dest_iata).upper()

                key = (airline.lower(), origin, dest)
                url = api_url_map.get(key)

                if url:
                    # Override URL with real Google Flights URL
                    f["url"] = url

                enriched.append(f)

            state.flights = enriched
        else:
            # If LLM didn't produce any flights, fallback to API flights
            fallback_flights = []
            for (airline_lower, o, d), url in api_url_map.items():
                airline_name = airline_lower.title()
                fallback_flights.append(
                    {
                        "airline": airline_name,
                        "origin": o,
                        "destination": d,
                        "price": None,  # we don't get real prices from API
                        "url": url,
                    }
                )
            # Keep at most 5
            state.flights = fallback_flights[:5]

        return state

    except Exception as e:
        print(f"⚠️ Error calling AviationStack: {e!r}")
        # On error, just keep whatever flights we already have (LLM ones)
        return state