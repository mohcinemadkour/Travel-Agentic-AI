# agents/destination_utils.py
"""
Resolve destination for hotel search.
When user provides an airport code (e.g. BOM, BLR), resolve to city name
so hotel APIs return relevant results.
Uses airports.csv when available; falls back to Aviation Edge API or static mapping.
"""

import csv
import os
import requests

# Fallback when airports.csv not found (minimal set)
_FALLBACK_IATA_TO_CITY = {
    "BOM": "Mumbai",
    "BLR": "Bengaluru",
    "DEL": "New Delhi",
    "MAA": "Chennai",
    "HYD": "Hyderabad",
    "CCU": "Kolkata",
    "JFK": "New York",
    "LHR": "London",
    "CDG": "Paris",
    "DXB": "Dubai",
    "SIN": "Singapore",
    "BKK": "Bangkok",
    "HKG": "Hong Kong",
    "ICN": "Seoul",
    "NRT": "Tokyo",
    "HND": "Tokyo",
    "SYD": "Sydney",
    "LAX": "Los Angeles",
    "SFO": "San Francisco",
}


def _load_iata_to_city_from_csv() -> dict[str, str]:
    """Load IATA → city mapping from airports.csv. Prefer large/medium airports."""
    iata_to_city: dict[str, tuple[str, int]] = {}  # city, priority (higher = prefer)
    priority = {"large_airport": 3, "medium_airport": 2, "small_airport": 1}

    for base in (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.getcwd()):
        path = os.path.join(base, "airports.csv")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        iata = (row.get("iata_code") or "").strip()
                        city = (row.get("municipality") or "").strip()
                        if iata and len(iata) == 3 and iata.isalpha() and city:
                            p = priority.get(row.get("type", ""), 0)
                            if iata not in iata_to_city or p > iata_to_city[iata][1]:
                                iata_to_city[iata] = (city, p)
                return {k: v[0] for k, v in iata_to_city.items()}
            except Exception:
                pass
            break
    return {}


# Load from CSV at module load; fallback to static if CSV missing
_IATA_TO_CITY_CACHE: dict[str, str] | None = None


def _get_iata_to_city() -> dict[str, str]:
    """Get IATA_TO_CITY mapping (from CSV or fallback)."""
    global _IATA_TO_CITY_CACHE
    if _IATA_TO_CITY_CACHE is None:
        _IATA_TO_CITY_CACHE = _load_iata_to_city_from_csv()
        if not _IATA_TO_CITY_CACHE:
            _IATA_TO_CITY_CACHE = _FALLBACK_IATA_TO_CITY.copy()
    return _IATA_TO_CITY_CACHE


def _looks_like_iata(text: str) -> bool:
    """Check if input looks like an IATA airport code (3 letters)."""
    if not text or len(text) != 3:
        return False
    return text.strip().isalpha()


def _fetch_city_from_aviation_edge(iata: str) -> str | None:
    """Fetch city name from Aviation Edge airport database."""
    api_key = os.getenv("AVIATION_EDGE_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        return None
    url = "https://aviation-edge.com/v2/public/airportDatabase"
    params = {"key": api_key, "codeIataAirport": iata.upper()}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        airport = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else None)
        if not airport:
            return None
        city = (
            airport.get("cityName")
            or airport.get("nameCity")
            or airport.get("city")
        )
        if city and isinstance(city, str) and city.strip():
            return city.strip()
        name = airport.get("name") or airport.get("nameAirport") or ""
        if isinstance(name, str) and name:
            first = name.split()[0] if name.split() else ""
            if len(first) > 2 and first[0].isupper():
                return first
    except Exception:
        pass
    return None


def resolve_destination_for_hotels(destination: str) -> str:
    """
    Resolve destination to a city name suitable for hotel search.
    - If destination looks like IATA (3 letters): resolve to city name.
    - Otherwise: return as-is (assume it's already a city/place name).
    """
    if not destination:
        return ""
    dest = destination.strip()
    if not _looks_like_iata(dest):
        return dest

    iata = dest.upper()
    iata_to_city = _get_iata_to_city()
    city = iata_to_city.get(iata)
    if city:
        return city
    city = _fetch_city_from_aviation_edge(iata)
    if city:
        return city
    return dest
