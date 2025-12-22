# main.py — AI Travel Agent (CLI)

Purpose
- Entrypoint for a small AI travel planning workflow built on a LangGraph-style graph.
- Collects travel inputs, builds & invokes the graph, and prints summarized results (weather, hotels, flights).

How it works
- Loads environment variables via `python-dotenv`.
- Imports `build_graph()` from `graph` and `TravelState` from `state`.
- Builds an initial `TravelState` with the provided inputs and calls `graph.invoke(initial_state)`.
- Normalizes the returned `final_state` (if it's a `TravelState`) to a dictionary and prints:
  - Weather summary (`weather_summary`)
  - Recommended accommodations (`recommended_hotels`)
  - Flight options (`flights`)

Inputs
- origin: airport code or city string (e.g., `BLR`)
- destination: city or region (e.g., `Mumbai`)
- start_date / end_date: ISO date strings (`YYYY-MM-DD`)
- bedrooms: integer (default 1)
- max_price_per_night: float (default 200)
- min_rating: float (default 4.0)

Outputs
- Printed sections to stdout:
  - `=== WEATHER ===` — human-readable weather summary if available.
  - `=== TOP HOTELS ===` — list of hotels with `name`, `rating`, `price` and `url`.
  - `=== TOP FLIGHTS ===` — list of flights with `airline`, `origin`, `destination`, `price`, and `url`.
    - `=== TOP FLIGHTS ===` — list of flights with `airline`, `origin`, `destination`, departure/arrival `time` when available, `price`, and `url`.

Notes & running non-interactively
- The file includes an interactive prompt branch (commented out) and a non-interactive example that sets defaults for quick runs.
- To run non-interactively (example):
  ```bash
  python main.py
  ```

- To run interactively, uncomment the `input()` lines and run:
  ```bash
  python main.py
  ```

Dependencies
- `python-dotenv` — loads `.env` for API keys and DB credentials.
- `langgraph` or the project's `graph.py` implementation — builds and runs the workflow.
- `singlestoredb` (optional) — used by the project's caching/DB helpers if enabled.

Troubleshooting
- If `graph.invoke()` raises import or runtime errors, ensure the graph and its agents (weather, flights, hotels) are available and any required API keys are present in `.env`.
- DB column mismatches (e.g., `city` vs `location_city`) were previously fixed in `database` helpers; verify your DB schema matches code.

Where to look next
- `graph.py` — graph definition and agent wiring.
- `state.py` — `TravelState` model definition.
- `streamlit_app.py` — Streamlit UI wrapper around the same workflow.

Maintainer notes
- The repo contains a `run_main_test.py` helper that stubs external dependencies and runs a mocked, non-interactive execution useful for CI or development without API keys.
# main.py — AI Travel Agent (CLI Entrypoint)

## Purpose

`main.py` is the command-line entrypoint for the Agentic AI Travel Agent. It:
- Loads environment variables from a `.env` file.
- Collects travel parameters interactively from the user.
- Builds and invokes the LangGraph workflow (via `build_graph`).
- Prints a concise summary of weather, top hotel recommendations, and flight options.

## Location
- Source: [main.py](main.py)
- Related: [graph.py](graph.py), [state.py](state.py)

## High-level flow
1. Call `load_dotenv()` to load environment variables.
2. Prompt the user for:
   - Origin (e.g., `BLR`)
   - Destination (e.g., `Mumbai`)
   - Start and end dates (`YYYY-MM-DD`)
   - Bedrooms (integer, default 1)
   - Max price per night (float, default 200)
   - Minimum hotel rating (float, default 4.0)
3. Instantiate a `TravelState` with the collected inputs.
4. Create the LangGraph with `build_graph()` and invoke it with the `TravelState`.
5. Convert the final state to a plain dict (calls `model_dump()` if the result is a `TravelState`).
6. Read keys from the final state and print three sections: `WEATHER`, `TOP HOTELS`, `TOP FLIGHTS`.

## Inputs (interactive)
- `origin`: string (airport code or city)
- `destination`: string (city or airport)
- `start_date`, `end_date`: strings in `YYYY-MM-DD` format
- `bedrooms`: integer (defaults to 1)
- `max_price_per_night`: float (defaults to 200)
- `min_rating`: float (defaults to 4.0)

## Expected output structure (from the graph)
The graph's final state is expected to include:
- `weather_summary`: string summarizing forecast for the dates/locations
- `recommended_hotels`: list of hotel dicts, each containing `name`, `rating`, `price` or `price_per_night`, and `url`
- `flights`: list of flight dicts, each containing `airline`, `origin`, `destination`, `price`, and `url`

## Printing format
- Weather: prints the `weather_summary` or a fallback message.
- Hotels: iterates `recommended_hotels` printing `- {name} — ⭐ {rating} — {price} per night → {url}`. Price is normalized to two decimals when possible; non-numeric prices are shown as `N/A`.
- Flights: iterates `flights` printing `- {airline} {origin} → {destination} — {price} → {url}`.

## Environment variables
`main.py` itself only calls `load_dotenv()`; the graph and agents expect the following environment variables (see `README.md` for full setup):
- `OPENAI_API_KEY` — required for LLM calls.
- `S2_HOST`, `S2_USER`, `S2_PASSWORD`, `S2_DB` — SingleStore connection (if using the DB cache).
- `AVIATIONSTACK_API_KEY` — optional (for real flight API queries).

Ensure a `.env` is present or the variables are otherwise set in the environment.

## How to run
From the project root:

```bash
python main.py
```

The program runs interactively and will prompt for the required inputs.

## Example session

User input (example):
```
Origin (e.g., BLR): BLR
Destination (e.g., Mumbai): BOM
Start date (YYYY-MM-DD): 2026-01-10
End date (YYYY-MM-DD): 2026-01-15
Bedrooms (default 1): 1
Max price per night (default 200): 150
Min rating (default 4.0): 4.2
```

Output (abridged):

```
=== WEATHER ===
Light rain expected on some days; pack an umbrella.

=== TOP HOTELS ===
- Hotel Plaza — ⭐ 4.5 — 120.00 per night → https://example.com/hotel/123

=== TOP FLIGHTS ===
- ExampleAir BLR → BOM — 85.0 → https://example.com/flight/456

🎉 Done! Your LangGraph-powered travel planning run is complete.
```

## Notes & pointers for maintainers
- The heavy lifting (API calls, caching, LLM fallbacks) is implemented inside the agents and the graph built in `graph.py`. Use that file to extend or tweak the workflow.
- `TravelState` is defined in `state.py` — modify its fields there if you need additional state carried through the graph.
- `main.py` intentionally keeps presentation and I/O simple; consider extracting printing and I/O to helper utilities if you need testing or non-interactive execution.

----
This document was generated from the `main.py` entrypoint to help new contributors understand how to run and extend the CLI.
