# Deploying to Render (Docker)

This guide shows how to deploy the Streamlit app to Render using the repository's `Dockerfile`.

Prerequisites
- A Render account (https://render.com) and connected GitHub/Git provider.

Steps

1. Push your repository to GitHub (branch `main` or change in `render.yaml`).

2. In Render dashboard, create a new "Web Service" and choose the Docker option.
   - Connect your repo and select the branch (e.g., `main`).
   - For the Dockerfile path, use `Dockerfile` (repo root).
   - Set the plan (Starter/Standard) as appropriate.

3. Environment variables and secrets
   - Add any required secrets (OpenAI key, SingleStore credentials) in Render's Environment section. Do NOT commit secrets to the repo.
   - The app reads `.env` locally; on Render, add keys as environment variables with the same names (e.g., `OPENAI_API_KEY`, `S2_HOST`, `S2_USER`, `S2_PASSWORD`, `S2_DB`).

4. Port handling
   - Render provides the `$PORT` environment variable. The project's `Dockerfile` uses `$PORT` at runtime, so no extra configuration is normally required.

5. Deploy
   - Start the deploy. Watch build logs for dependency installation and container startup.
   - After deploy, open the service URL provided by Render to access the Streamlit UI.

Notes & troubleshooting
- If build fails due to native wheels (pandas/numpy), the Docker image installs build-essential and uses pip; builds on Render's builders should succeed.
- For sensitive DB connections, restrict access to the DB from Render's IPs or configure a private network.
