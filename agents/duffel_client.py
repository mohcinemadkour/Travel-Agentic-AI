# agents/duffel_client.py
"""
Duffel API client for real flight prices.
Uses offer_requests endpoint to search for flights with live pricing.
"""

import os
import requests


def _google_flights_url(origin: str, dest: str, start: str | None, end: str | None) -> str:
    """Build Google Flights URL that pre-fills route and shows flight options."""
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


def fetch_flights_from_duffel(
    origin_iata: str,
    dest_iata: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    max_connections: int = 1,
    cabin_class: str = "economy",
    limit: int = 10,
) -> list[dict]:
    """
    Fetch flight offers with real prices from Duffel API.
    Returns list of dicts: {airline, origin, destination, price, total_currency, departure_time, arrival_time, url}
    """
    api_key = os.getenv("DUFFEL_API_KEY")
    if not api_key:
        return []

    url = "https://api.duffel.com/air/offer_requests"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Duffel-Version": "v2",
        "Authorization": f"Bearer {api_key}",
    }

    slices = [
        {
            "origin": origin_iata.upper(),
            "destination": dest_iata.upper(),
            "departure_date": departure_date,
        }
    ]
    if return_date:
        slices.append(
            {
                "origin": dest_iata.upper(),
                "destination": origin_iata.upper(),
                "departure_date": return_date,
            }
        )

    passengers = [{"type": "adult"} for _ in range(max(1, adults))]

    payload = {
        "data": {
            "slices": slices,
            "passengers": passengers,
            "cabin_class": cabin_class,
            "max_connections": max_connections,
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[Info] Duffel API: {e!r}")
        return []

    inner = data.get("data") or data
    offers = inner.get("offers") or []
    flights = []
    seen: set[tuple[str, float]] = set()

    for offer in offers[:limit]:
        airline = ""
        dep_time = ""
        arr_time = ""
        origin = origin_iata.upper()
        dest = dest_iata.upper()

        owner = offer.get("owner") or {}
        airline = owner.get("name") or owner.get("iata_code") or ""

        total_amount = offer.get("total_amount")
        total_currency = offer.get("total_currency") or "USD"
        try:
            price = float(total_amount) if total_amount is not None else None
        except (TypeError, ValueError):
            price = None

        # Dedupe by airline+price
        key = (airline, price or 0)
        if key in seen:
            continue
        seen.add(key)

        # Extract times from first segment
        for sl in offer.get("slices") or []:
            for seg in sl.get("segments") or []:
                dep_time = dep_time or seg.get("departing_at", "")
                arr_time = arr_time or seg.get("arriving_at", "")
                if not airline and seg.get("operating_carrier"):
                    airline = (seg.get("operating_carrier") or {}).get("name") or ""
                if seg.get("origin", {}).get("iata_code"):
                    origin = seg["origin"]["iata_code"]
                if seg.get("destination", {}).get("iata_code"):
                    dest = seg["destination"]["iata_code"]
                break
            if dep_time:
                break

        url_flight = _google_flights_url(origin, dest, departure_date, return_date)

        flights.append({
            "airline": airline,
            "origin": origin,
            "destination": dest,
            "price": price,
            "total_currency": total_currency,
            "departure_time": dep_time[:16] if dep_time else None,
            "arrival_time": arr_time[:16] if arr_time else None,
            "url": url_flight,
        })

    return flights
