# 🌍 AI Travel Agent (LangGraph Edition)

An **agentic travel planner** built around a LangGraph-style workflow. It:

- **Generates** hotels + flights with OpenAI (LLM)
- **Fetches** a simple weather summary (Open‑Meteo)
- **Optionally caches** results in SingleStore
- Provides both a **Streamlit UI** (`streamlit_app.py`) and a **CLI demo** (`main.py`)

Related docs:

- **Architecture**: `docs/agent_architecture.md`
- **Deploy**: `docs/deploy.md`, `docs/deploy_render.md`

Live demo: `https://travel-agentic-ai.onrender.com/`

---

## 🚀 Quickstart (recommended: Streamlit UI)

### Prereqs

- Python 3.11+
- An OpenAI API key

### Install

```bash
git clone https://github.com/pavanbelagatti/Agentic-AI-Travel-Agent.git
cd Agentic-AI-Travel-Agent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install streamlit
copy .env.example .env
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`.

### Run

```bash
streamlit run streamlit_app.py
```

Then open `http://localhost:8501`.

---

## 🧪 CLI (developer/demo)

The CLI entrypoint is `main.py`. It currently runs with **hardcoded demo inputs** (interactive `input()` lines are present but commented out).

```bash
python main.py
```

---

## 🔧 Environment variables

These names match what the code reads (`agents/*`, `database/*`):

- **Required**
  - `OPENAI_API_KEY`: used by `agents/search_agent.py`
- **Optional**
  - `OPENAI_CHAT_MODEL`: defaults to `gpt-4.1-mini`
  - `SERPAPI_API_KEY`: real hotel prices from [SerpAPI Google Hotels](https://serpapi.com/google-hotels-api) (preferred when dates are set)
  - `GOOGLE_PLACES_API_KEY` (or `GOOGLE_MAPS_API_KEY`): hotel data with photos & ratings from [Google Places](https://developers.google.com/maps/documentation/places)
  - `DUFFEL_API_KEY`: real flight prices from [Duffel](https://duffel.com) (preferred when dates are set)
  - `AVIATION_EDGE_API_KEY` (or `AVIATIONSTACK_API_KEY`): flight routes from [Aviation Edge](https://aviation-edge.com/developers)
  - `S2_HOST`, `S2_USER`, `S2_PASSWORD`, `S2_DB`: enables SingleStore caching (`database/cache.py`, `database/store_results.py`)

Use `.env.example` as a template:

```bash
copy .env.example .env
```

For deployments (Render/Streamlit Cloud), set the same variables in the platform environment settings (don’t upload `.env`).

---

## 🗄️ SingleStore setup (optional cache)

If you want caching enabled, create these tables in your SingleStore database.

### `accommodations`

```sql
CREATE TABLE IF NOT EXISTS accommodations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(100),
    provider_item_id VARCHAR(200),
    name VARCHAR(255),
    location_city VARCHAR(255),
    location_country VARCHAR(255),
    bedrooms INT,
    price_per_night DOUBLE,
    rating DOUBLE,
    url TEXT,
    vector BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `flights`

```sql
CREATE TABLE IF NOT EXISTS flights (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(100),
    airline VARCHAR(200),
    origin VARCHAR(10),
    destination VARCHAR(10),
    depart_time VARCHAR(50),
    arrive_time VARCHAR(50),
    price DOUBLE,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🐳 Docker

### Build & run

```bash
docker build -t travel-agent:latest .
docker run -p 8501:8501 --env-file .env --rm travel-agent:latest
```

### docker-compose

```bash
docker-compose up --build
```

---

## 🗂️ Repo layout (high-level)

- `streamlit_app.py`: Streamlit UI entrypoint
- `main.py`: CLI/demo entrypoint
- `graph.py`: workflow wiring (nodes + edges)
- `state.py`: `TravelState` schema passed between agents
- `agents/`: weather, LLM “live search”, recommendation, flight enrichment
  - `agents/serpapi_client.py`: SerpAPI Google Hotels (real prices)
  - `agents/places_client.py`: Google Places hotel search (photos/ratings/Maps links)
- `database/`: SingleStore connector + cache read/write
