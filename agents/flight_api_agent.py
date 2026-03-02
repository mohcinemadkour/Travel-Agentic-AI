# agents/flight_api_agent.py

import os
import requests

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
    """Build Google Flights URL that pre-fills route and shows results."""
    o = (origin or "").upper().strip()[:3]
    d = (dest or "").upper().strip()[:3]
    if not o or not d:
        return "https://www.google.com/travel/flights"
    base = f"https://www.google.com/travel/flights/flights-from-{o.lower()}-to-{d.lower()}.html"
    if start or end:
        params = []
        if start:
            params.append(f"outbound_date={start}")
        if end:
            params.append(f"return_date={end}")
        if params:
            base += "?" + "&".join(params)
    return base


def _flight_url_for_display(
    airline: str,
    origin: str,
    dest: str,
    start: str | None,
    end: str | None,
) -> str:
    """
    Build URL that directs to the specific flight (airline + route + dates).
    Uses Google search for "{airline} flights {origin} to {dest} {dates}"
    which surfaces a Flights onebox linking to that airline's options.
    """
    from urllib.parse import quote_plus

    o = (origin or "").upper().strip()[:3]
    d = (dest or "").upper().strip()[:3]
    if not o or not d:
        return _google_flights_url(origin, dest, start, end)

    airline_clean = (airline or "").strip().lower()

    # Google search for "{airline} flights {origin} to {dest} {dates}" surfaces
    # a Flights onebox that links to that airline's options for the route
    if airline_clean:
        q_parts = [(airline or "").strip(), "flights", o, "to", d]
        if start:
            q_parts.append(start)
        if end:
            q_parts.append(end)
        q = " ".join(str(p) for p in q_parts if p)
        return f"https://www.google.com/search?q={quote_plus(q)}"
    return _google_flights_url(origin, dest, start, end)


def _normalize_airline(name: str) -> str:
    """Normalize airline name for matching (LLM vs API may differ)."""
    if not name:
        return ""
    return name.lower().strip().replace(" ", "").replace("-", "")


def _ensure_flight_urls(state, origin_iata: str, dest_iata: str) -> None:
    """Ensure every flight has a URL that directs to that specific flight (airline + route + dates)."""
    flights = state.flights or []
    for f in flights:
        o = (f.get("origin") or origin_iata).upper()
        d = (f.get("destination") or dest_iata).upper()
        airline = f.get("airline") or ""
        f["url"] = _flight_url_for_display(airline, o, d, state.start_date, state.end_date)
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
    Use Duffel (real prices) > Aviation Edge (routes) to discover flights.
    When DUFFEL_API_KEY is set and dates available, fetches real flight prices.
    """

    origin_iata = _city_to_iata(state.origin or "")
    dest_iata = _city_to_iata(state.destination or "")

    if not origin_iata or not dest_iata:
        print("[Warning] Missing origin/destination IATA codes.")
        _ensure_flight_urls(state, origin_iata or "XXX", dest_iata or "XXX")
        return state

    # Duffel: real flight prices when key + dates available
    if os.getenv("DUFFEL_API_KEY") and state.start_date:
        try:
            from agents.duffel_client import fetch_flights_from_duffel

            duffel_flights = fetch_flights_from_duffel(
                origin_iata=origin_iata,
                dest_iata=dest_iata,
                departure_date=state.start_date,
                return_date=state.end_date,
                adults=1,
                limit=10,
            )
            if duffel_flights:
                state.flights = duffel_flights
                _ensure_flight_urls(state, origin_iata, dest_iata)
                return state
        except Exception as e:
            print(f"[Info] Duffel API: {e!r} (falling back to Aviation Edge)")

    # Aviation Edge: routes only (no prices)
    api_key = os.getenv("AVIATION_EDGE_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        _ensure_flight_urls(state, origin_iata, dest_iata)
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
    _ensure_flight_urls(state, origin_iata, dest_iata)

    return state