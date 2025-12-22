import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def live_search(state):
    """
    Use OpenAI Chat Completions to generate accommodations + flights
    consistent with the user's inputs.

    - No hard-coded results.
    - Prints raw LLM output for debugging.
    - Tries to be flexible if the model nests or renames keys.
    """
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
- Use realistic-sounding hotel names and airlines, but you may approximate.
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
- Max flight price (if provided): {state.max_flight_price}

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

        state.accommodations = accommodations
        state.flights = flights
        return state

    except Exception as e:
        print("⚠️ live_search error, leaving results empty:", repr(e))
        state.accommodations = []
        state.flights = []
        return state