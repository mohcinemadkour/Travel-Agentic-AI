"""
Pydantic models for API request/response schemas.
Decoupled from internal TravelState to allow the API contract to evolve independently.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


# ── Request models ──────────────────────────────────────────

class SearchRequest(BaseModel):
    origin: str = Field(..., min_length=1, examples=["JFK"])
    destination: str = Field(..., min_length=1, examples=["MCO"])
    start_date: str = Field(..., examples=["2026-04-30"])
    end_date: str = Field(..., examples=["2026-05-09"])
    bedrooms: int = Field(default=1, ge=1)
    max_price_per_night: float = Field(default=200.0, ge=0)
    min_rating: float = Field(default=4.0, ge=0, le=5)


# ── Response models ─────────────────────────────────────────

class HotelItem(BaseModel):
    name: str | None = None
    city: str | None = None
    country: str | None = None
    price: float | None = None
    rating: float | None = None
    url: str | None = None
    map_url: str | None = None
    photo_url: str | None = None


class SearchResponse(BaseModel):
    origin: str | None = None
    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    weather_summary: str | None = None
    recommended_hotels: list[HotelItem] = []


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
