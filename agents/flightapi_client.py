"""
FlightAPI client for flight prices (https://www.flightapi.io/).
Uses roundtrip or oneway endpoint with real-time pricing.
"""

import os
import requests


def _google_flights_url(origin: str, dest: str, start: str | None, end: str | None) -> str:
    """Build Google Flights URL (travel path) with route and optional dates."""
    def slug(s: str) -> str:
        if not s:
            return ""
        return s.strip().lower().replace(" ", "-")[:50]

    o = slug(origin or "") or "xxx"
    d = slug(dest or "") or "xxx"
    if o == "xxx" or d == "xxx":
        return "https://www.google.com/travel/flights"
    base = f"https://www.google.com/travel/flights/flights-from-{o}-to-{d}.html"
    params = []
    if start:
        params.append(f"outbound_date={start}")
    if end:
        params.append(f"return_date={end}")
    if params:
        base += "?" + "&".join(params)
    return base


def fetch_flights_from_flightapi(
    origin_iata: str,
    dest_iata: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    cabin_class: str = "Economy",
    currency: str = "USD",
) -> list[dict]:
    """
    Fetch flight offers with prices from FlightAPI.
    Returns top 3 cheapest per airline, all airlines included, sorted by price.
    """
    api_key = os.getenv("FLIGHTAPI_API_KEY")
    if not api_key:
        return []

    # Round trip: /roundtrip/{api_key}/{dep}/{arr}/{dep_date}/{arr_date}/{adults}/0/0/{cabin}/{currency}
    # One way: /onewaytrip/{api_key}/{dep}/{arr}/{dep_date}/{adults}/0/0/{cabin}/{currency}
    dep = origin_iata.upper().strip()[:3]
    arr = dest_iata.upper().strip()[:3]
    if not dep or not arr:
        return []

    if return_date:
        url = (
            f"https://api.flightapi.io/roundtrip/{api_key}/{dep}/{arr}/"
            f"{departure_date}/{return_date}/{adults}/0/0/{cabin_class}/{currency}"
        )
    else:
        url = (
            f"https://api.flightapi.io/onewaytrip/{api_key}/{dep}/{arr}/"
            f"{departure_date}/{adults}/0/0/{cabin_class}/{currency}"
        )

    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 403:
            print("[Warning] FlightAPI: API quota exceeded. Upgrade plan or wait for reset.")
            return []
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[Info] FlightAPI: {e!r}")
        return []

    if data.get("status") != 0 and data.get("status") is not None:
        print(f"[Info] FlightAPI: status={data.get('status')}, msg={data.get('msg', '')}")
        return []

    itineraries = data.get("itineraries") or []
    legs_by_id = {leg["id"]: leg for leg in data.get("legs") or []}
    carriers_by_id = {c.get("id"): c for c in data.get("carriers") or []}

    # Collect all valid flights, dedup by (airline, price)
    all_flights: list[dict] = []
    seen: set[tuple[str, float]] = set()
    per_airline = 3  # top N cheapest per airline

    for itin in itineraries:
        cheapest = itin.get("cheapest_price") or {}
        amount = cheapest.get("amount")
        if amount is None:
            continue
        try:
            price = float(amount)
        except (TypeError, ValueError):
            continue

        airline = ""
        dep_time = ""
        arr_time = ""
        leg_ids = itin.get("leg_ids") or []
        if leg_ids:
            first_leg = legs_by_id.get(leg_ids[0]) or {}
            carrier_ids = first_leg.get("marketing_carrier_ids") or []
            if carrier_ids:
                carrier = carriers_by_id.get(carrier_ids[0]) or {}
                airline = carrier.get("name") or carrier.get("iata") or ""
            dep_time = first_leg.get("departure") or ""
            arr_time = first_leg.get("arrival") or ""

        airline_key = (airline or "unknown").strip().lower()
        dedup_key = (airline_key, price)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Extract booking deeplink from pricing_options
        booking_url = ""
        for po in itin.get("pricing_options") or []:
            for item in po.get("items") or []:
                raw_url = (item.get("url") or "").strip()
                if raw_url:
                    if raw_url.startswith("/"):
                        booking_url = f"https://www.skyscanner.com{raw_url}"
                    elif raw_url.startswith("http"):
                        booking_url = raw_url
                    break
                for field in ("deeplink", "direct_link", "booking_url"):
                    dl = (item.get(field) or "").strip()
                    if dl and dl.startswith("http"):
                        booking_url = dl
                        break
                if booking_url:
                    break
            if booking_url:
                break

        if not booking_url:
            booking_url = _google_flights_url(dep, arr, departure_date, return_date)

        all_flights.append({
            "airline": airline or "—",
            "origin": dep,
            "destination": arr,
            "price": price,
            "total_currency": currency,
            "departure_time": dep_time[:16] if dep_time else None,
            "arrival_time": arr_time[:16] if arr_time else None,
            "url": booking_url,
        })

    # For each airline, keep only the top 3 cheapest offers
    all_flights.sort(key=lambda f: f["price"])
    airline_count: dict[str, int] = {}
    flights: list[dict] = []
    for f in all_flights:
        key = (f["airline"] or "unknown").strip().lower()
        cnt = airline_count.get(key, 0)
        if cnt >= per_airline:
            continue
        airline_count[key] = cnt + 1
        flights.append(f)

    return flights
