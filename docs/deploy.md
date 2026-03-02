# Deploying the Streamlit App

This document explains simple ways to deploy the `streamlit_app.py` from this repository.

Options

- Streamlit Cloud (recommended for quick public deploys)
- Docker (recommended for local or server deployment)

1) Streamlit Cloud

- Push this repository to GitHub.
- Sign in to Streamlit Cloud (https://share.streamlit.io) and link your GitHub repo.
- Select the repository and branch; set the app file to `streamlit_app.py` and deploy.

Notes:
- Ensure your secrets (OpenAI key, DB creds) are stored in Streamlit Cloud's Secret Manager — do NOT commit secrets to the repo.

2) Docker (local or server)

Prerequisites:
- Docker installed on the host.

Build and run locally (from repo root):
```bash
docker build -t travel-agent:latest .
docker run -p 8501:8501 --env-file .env --rm travel-agent:latest
```

Using docker-compose:
```bash
docker-compose up --build
```

3) Notes about dependencies

- On Windows (especially ARM), `pip install streamlit` may require build tools (MSVC) or using conda packages from `conda-forge`.
- If installation fails on Windows, consider building the Docker image in a Linux environment or use `conda` locally:
  ```bash
  conda install -c conda-forge streamlit
  pip install -r requirements.txt
  ```

4) Environment variables and secrets

- Locally, create `.env` from `.env.example` and fill in real values.
- For Docker, provide your `.env` file to the container via `--env-file` (local) or configure secrets in the hosting provider.
- With `docker-compose`, either:
  - add an `env_file: .env` entry to `docker-compose.yml`, or
  - set the variables in the Compose service `environment:` section, or
  - export them in your shell before running Compose.

Common variables:

- `OPENAI_API_KEY` (required)
- `OPENAI_CHAT_MODEL` (optional)
- `GOOGLE_PLACES_API_KEY` / `GOOGLE_MAPS_API_KEY` (optional; enables Google Places + Geocoding for real hotel data)
- `AVIATION_EDGE_API_KEY` (optional; enables Aviation Edge routes enrichment for flights; also supports legacy `AVIATIONSTACK_API_KEY`)
- `S2_HOST`, `S2_USER`, `S2_PASSWORD`, `S2_DB` (optional)

5) Verifying the app

- After deployment, open `http://localhost:8501` (or the host URL) to confirm the app loads.
