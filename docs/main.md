# `main.py` (CLI / demo entrypoint)

## What it does

`main.py` runs the same agent workflow as the Streamlit app, but prints results to stdout:

- `weather_summary`
- top hotel recommendations (`recommended_hotels`)
- top flight options (`flights`)

Under the hood it:

- loads env vars via `python-dotenv`
- builds the workflow from `graph.build_graph()`
- passes a `TravelState` through the agents

## How to run

From the repo root:

```bash
python main.py
```

## Important note about inputs

Right now `main.py` is set up as a **non-interactive demo**: it uses hardcoded values for origin/destination/dates.

If you want an interactive CLI:

- open `main.py`
- uncomment the `input()` lines near the top of `main()`
- remove or override the hardcoded demo values

## Environment variables

Same as the rest of the project (see `.env.example`):

- `OPENAI_API_KEY` (required)
- `OPENAI_CHAT_MODEL` (optional)
- `GOOGLE_PLACES_API_KEY` / `GOOGLE_MAPS_API_KEY` (optional; enables Google Places + Geocoding for real hotel data)
- `AVIATION_EDGE_API_KEY` (optional; enables Aviation Edge routes enrichment for flights; also supports legacy `AVIATIONSTACK_API_KEY`)
- `S2_HOST`, `S2_USER`, `S2_PASSWORD`, `S2_DB` (optional)

## Related files

- `streamlit_app.py`: UI entrypoint
- `graph.py`: workflow wiring
- `state.py`: `TravelState`
- `agents/`: weather + LLM hotel/flight generation + recommendation steps
- `database/`: SingleStore caching utilities

## Troubleshooting

- If you see OpenAI auth errors, confirm `OPENAI_API_KEY` is set in `.env` (or your environment).
- If SingleStore isn’t configured, the workflow should still run, but caching will be skipped (see `database/singlestore_client.py`).
