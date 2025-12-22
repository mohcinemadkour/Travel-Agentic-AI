FROM python:3.11-slim

# Install system build deps (helps with packages like pandas)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git curl libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Streamlit is installed (in case not in requirements)
RUN pip install --no-cache-dir streamlit

# Copy app
COPY . /app

ENV PORT=8501
EXPOSE 8501

# Use shell form so $PORT is expanded at runtime (Render provides $PORT)
CMD sh -c "streamlit run streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0"
