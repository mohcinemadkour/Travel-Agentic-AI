# Dev Branch Changes Summary

## Overview

1. **UI Redesign as TravelTwin Digital Assistant**
2. **FastAPI Backend Decoupling**
3. **Flight Section Removed**

---

## 1. UI Redesign — TravelTwin Digital Assistant

### Theme & Branding
- Renamed from "AI Travel Agent" to **TravelTwin**.
- Bot avatar using DiceBear API.
- Dark gradient sidebar with white input fields.
- Hero banner with gradient background.

### Layout
- **Sidebar**: All search inputs moved to a collapsible sidebar (From, To, dates, rooms, price, rating).
- **Main area**: Clean results display with section headers and icons.

### Hotel Cards
- Card-based layout in 3-column grid.
- Numbered rank badges (circled numbers).
- Visual star ratings.
- Green price badges.
- "View on map" and "Book now" pill buttons with hover effects.
- Photo display when available from Google Places.

### Assistant Messages
- Blue-accented message bubbles for welcome text and trip summary.
- Weather displayed in a purple gradient card.

### Files Modified
| File | Changes |
|------|---------|
| `streamlit_app.py` | Complete UI rewrite with custom CSS and HTML rendering |

---

## 2. FastAPI Backend Decoupling

### Architecture
The business logic is now accessible through a **REST API** (FastAPI), decoupled from the Streamlit UI.

```
Streamlit UI  ──HTTP──>  FastAPI Backend  ──>  LangGraph Workflow
   (port 8501)            (port 8000)           (agents, APIs, cache)
```

### New Files
| File | Purpose |
|------|---------|
| `api/__init__.py` | Package init |
| `api/app.py` | FastAPI application with CORS middleware |
| `api/models.py` | Pydantic request/response schemas (SearchRequest, SearchResponse, etc.) |
| `api/routes.py` | API route definitions (/health, /search) |
| `api/service.py` | Async service layer bridging API to LangGraph (thread pool for blocking calls) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/search` | Full travel search (weather + hotels) |

### Streamlit Changes
- `streamlit_app.py` no longer imports agents or graph directly.
- Calls FastAPI via HTTP (`requests.post`).
- API base URL configurable via `TRAVELTWIN_API_URL` env var (defaults to `http://localhost:8000/api/v1`).

### Running the Decoupled Setup

```bash
# Terminal 1: Start the API backend
uvicorn api.app:app --host 0.0.0.0 --port 8000

# Terminal 2: Start the Streamlit frontend
streamlit run streamlit_app.py
```

### Interactive API Docs
With FastAPI running, visit `http://localhost:8000/docs` for the auto-generated Swagger UI.

---

## 3. Flight Section Removed

All flight-related functionality has been removed from the application:

### Deleted Files
| File | Was |
|------|-----|
| `agents/flightapi_client.py` | FlightAPI.io client |
| `agents/flight_api_agent.py` | Flight API orchestration agent |
| `agents/flights_agent.py` | Flight recommendation agent |
| `agents/duffel_client.py` | Duffel API client |
| `agents/parallel_search.py` | Parallel hotel + flight search |
| `tests/test_flights_newyork_dfw.py` | Flight test |

### API Keys No Longer Needed
| Variable | Was Used For |
|----------|-------------|
| `FLIGHTAPI_API_KEY` | FlightAPI.io real-time flight prices |
| `DUFFEL_API_KEY` | Duffel flight prices (fallback) |
| `AVIATION_EDGE_API_KEY` | Airport code resolution & flight routes |

IATA code resolution now uses the local `airports.csv` / `airport-codes.csv` files instead of the Aviation Edge API.

---

## Environment Variables

### Current
| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | LLM hotel generation |
| `SERPAPI_API_KEY` | Google Hotels real prices |
| `GOOGLE_PLACES_API_KEY` | Hotel photos/ratings |
| `OPENAI_CHAT_MODEL` | LLM model override (default: gpt-4.1-mini) |
| `S2_HOST/USER/PASSWORD/DB` | SingleStore cache |
| `TRAVELTWIN_API_URL` | FastAPI backend URL for Streamlit (default: `http://localhost:8000/api/v1`) |
