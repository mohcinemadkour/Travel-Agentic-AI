# The Core Concept

Instead of one monolithic program, the system uses specialized AI agents that each handle specific tasks. These agents read from and write to the shared `TravelState`.

## How It Works Step-by-Step

1. Weather Agent (`fetch_weather`)
```python
# Example of what this agent might do:
def fetch_weather(state: TravelState):
    # 1. Read from state
    destination = state.destination
    dates = f"{state.start_date} to {state.end_date}"
    
    # 2. Call weather API/tool
    weather_data = call_weather_api(destination, dates)
    
    # 3. Generate human-readable summary using LLM
    summary = llm.generate(f"Summarize this weather: {weather_data}")
    
    # 4. Write back to state
    state.weather_summary = summary
    return state
```
Result: `weather_summary` field gets populated with text like "Sunny with highs of 25°C, light rain expected on Wednesday"

2. Hotel Search Agent (`live_search`)
```python
def live_search(state: TravelState):
    # 1. Read preferences from state
    location = state.destination
    max_price = state.max_price_per_night
    min_rating = state.min_rating
    
    # 2. Search hotels (using tools/APIs)
    raw_hotels = search_hotels_api(location, max_price, min_rating)
    
    # 3. Store raw results
    state.accommodations = raw_hotels  # All possible options
    return state
```
Result: `accommodations` gets a list of hotel dictionaries with raw data

3. Flight API Agent (`fetch_flights_from_api`)
```python
def fetch_flights_from_api(state: TravelState):
    # 1. Read travel details
    origin = state.origin
    destination = state.destination
    dates = (state.start_date, state.end_date)
    
    # 2. Call flight API
    flight_options = call_flight_api(origin, destination, dates)
    
    # 3. Store raw results
    state.flights = flight_options
    return state
```
Result: `flights` gets populated with available flight options

4. Recommendation Agents (Filtering/Curating)
```python
def recommend_hotels(state: TravelState):
    # 1. Read raw data
    all_hotels = state.accommodations
    
    # 2. Apply intelligent filtering/sorting with LLM
    filtered = llm.analyze(
        "Filter hotels by rating, price, and relevance",
        hotels=all_hotels,
        criteria={
            "max_price": state.max_price_per_night,
            "min_rating": state.min_rating,
            "bedrooms": state.bedrooms
        }
    )
    
    # 3. Write curated results
    state.recommended_hotels = filtered[:5]  # Top 5 recommendations
    return state
```
Result: `recommended_hotels` gets the best 5 hotels after filtering

## The Magic: State Passing Through Graph

START (user inputs)
    ↓
[weather agent] → adds `weather_summary`
    ↓
[cache check] → may skip ahead if cached
    ↓
[hotel search] → adds `accommodations` (raw)
    ↓  
[flight API] → adds `flights` (raw)
    ↓
[store cache] → saves for next time
    ↓
[recommend hotels] → transforms accommodations → `recommended_hotels`
    ↓
[recommend flights] → filters/sorts flights
    ↓
END (complete travel plan)

## What Makes It "Agent-Generated"?

- **Specialization:** Each agent does ONE job well

- **LLM-Powered:** Uses language models to understand/process/summarize

- **Tool Usage:** Agents can call external APIs/tools

- **State-Aware:** Each agent reads previous work and adds its contribution

- **Progressive Refinement:** Raw data → Filtered → Curated recommendations

## Example Final State
```python
TravelState(
    origin="BLR",
    destination="Mumbai",
    weather_summary="Mostly sunny, 28-32°C, 10% chance of rain",
    accommodations=[{raw hotel data...}],  # 50+ hotels
    flights=[{raw flight data...}],        # 20+ flights
    recommended_hotels=[{top 5 hotels...}], # Curated list
    # ... other fields
)
```

**Key Insight:** The `TravelState` starts as an empty container with just user inputs, and gets progressively filled by different agents as it flows through the graph!
