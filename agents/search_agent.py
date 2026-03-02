import json
import os
from openai import OpenAI

from agents.places_client import fetch_hotels_from_places

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def live_search(state):
    """
    Fetch accommodations (hotels) and flights.
    - Hotels: Google Places API when GOOGLE_PLACES_API_KEY is set, else LLM.
    - Flights: LLM (enriched later by Aviation Edge).
    """
    accommodations_from_places = []

    if os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY"):
        accommodations_from_places = fetch_hotels_from_places(
            destination=state.destination or "",
            max_price_per_night=state.max_price_per_night,
            min_rating=state.min_rating,
            bedrooms=state.bedrooms or 1,
            limit=10,
        )

    # LLM for flights (and hotels when Places not used)
    system_prompt = """
You are a travel planning AI. You help users find hotels and flights.

You MUST respond with STRICT JSON only. No markdown, no explanations, no comments.
The JSON MUST have this exact structure (field names should ideally match):

{
  "accommodations": [
    {
      "name": "string",
      "city": "string",
      "country": "string",
      "price": 120.0,
      "rating": 8.5,
      "bedrooms": 1,
      "url": "https://..."
    }
  ],
  "flights": [
    {
      "airline": "string",
      "origin": "string",
      "destination": "string",
      "price": 450.0,
      "url": "https://..."
    }
  ]
}

Rules:
- All numbers must be valid JSON numbers (no commas in thousands, e.g. 1565.0 not 1,565.0).
- Return 3–7 accommodations.
- Return 2–5 flights.
- Try to respect user constraints (max price, min rating, bedrooms, route).
- Use realistic hotel names and airlines for the destination.
- For hotel prices: use approximate USD per-night rates typical for that city and star level. Stay within the user's max_price when provided. Prefer conservative estimates (slightly lower than typical) since users will verify on booking sites.
    """.strip()

    user_prompt = f"""
User trip details:
- Origin: {state.origin}
- Destination: {state.destination}
- Start date: {state.start_date}
- End date: {state.end_date}
- Bedrooms needed: {state.bedrooms}
- Max hotel price per night: {state.max_price_per_night}
- Minimum hotel rating: {state.min_rating}
"""
    if state.max_flight_price is not None:
        user_prompt += f"- Max flight price: {state.max_flight_price}\n"

    user_prompt += """
Generate hotels and flights that match these constraints as much as possible.

Return ONLY the JSON object as specified in the system message.
Do NOT include any additional keys, text, or markdown.
    """.strip()

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        content = resp.choices[0].message.content.strip()

        print("\n--- RAW LLM OUTPUT (for debugging) ---")
        print(content)
        print("--- END RAW LLM OUTPUT ---\n")

        # Strip ```json fences if present
        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 3:
                content = parts[1]
            content = content.replace("json", "", 1).strip()

        cleaned = (
            content.replace(",}", "}")
                   .replace(",]", "]")
        )

        data = json.loads(cleaned)

        # If nested under "result"/"data"/"response"
        if isinstance(data, dict) and "accommodations" not in data and "flights" not in data:
            for key in ["result", "data", "response"]:
                if isinstance(data.get(key), dict):
                    data = data[key]
                    break

        accommodations = (
            data.get("accommodations")
            or data.get("hotels")
            or data.get("places")
            or []
        )

        flights = (
            data.get("flights")
            or data.get("flight_options")
            or data.get("routes")
            or []
        )

        if not isinstance(accommodations, list):
            accommodations = []
        if not isinstance(flights, list):
            flights = []

        # Use Google Places hotels when available; else LLM
        state.accommodations = accommodations_from_places if accommodations_from_places else accommodations
        state.flights = flights
        return state

    except Exception as e:
        print("[Warning] live_search error:", repr(e))
        state.accommodations = accommodations_from_places if accommodations_from_places else []
        state.flights = []
        return state