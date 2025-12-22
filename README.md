# 🌍 AI Travel Agent (LangGraph Edition)

A fully functional **Agentic AI Travel Planner** built using **LangGraph**, **OpenAI**, and **SingleStore**.

This AI system helps users:
- ✔️ Get hotel recommendations  
- ✔️ Find flights  
- ✔️ Fetch weather information  
- ✔️ Cache results in SingleStore. Get your [free SingleStore account](https://bit.ly/SingleStore-Agentic-App)  
- ✔️ Build reproducible agentic workflows  

All powered by a modular LangGraph graph with independent agents.

---

Live demo: https://travel-agentic-ai.onrender.com/


## 🚀 Features



For a detailed description of the agent architecture and step-by-step examples, see `docs/agent_architecture.md`.

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/pavanbelagatti/Agentic-AI-Travel-Agent.git
cd Agentic-AI-Travel-Agent.git
```

### Create a virtual environment
```
python3 -m venv venv
```

```python3 -m venv .venv
source .venv/bin/activate     # For Mac/Linux
OR
.\.venv\Scripts\activate      # For Windows
```

### Install dependencies 
```
pip install -r requirements.txt
```

### 🔧 Environment Variables

Copy `.env.example` to `.env` and fill in your real values locally. Do NOT commit your `.env` file to the repository.

```bash
cp .env.example .env
# then edit .env and add your secrets locally
```

If you are deploying to a platform (Render, Streamlit Cloud, etc.) add the same variables to the platform's secret manager or environment settings.

### 🗄️ Setting Up SingleStore

- [Signup & Log in to SingleStore Account](https://bit.ly/SingleStore-Agentic-App)
- Click Create Database → Name it TravelAG or whatever you wish to name it
- Open the SQL Editor in the SingleStore dashboard
- Run the following table creation queries:

#### Accommodations table
```
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

#### Flights table
```
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
These tables will remain empty initially — your LangGraph agents will store results into them automatically during the first run.

### Running the application
```
python main.py
```

#### You’ll be asked:
- Origin airport/city
- Destination
- Start & end dates
- Bedrooms
- Budget
- Minimum rating

#### After the LangGraph workflow completes, you’ll get:
- Weather summary
- Top hotel recommendations
- Top flight options
