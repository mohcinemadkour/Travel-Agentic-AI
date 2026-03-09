"""
FastAPI route definitions.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import (
    SearchRequest,
    SearchResponse,
    HotelItem,
    HealthResponse,
)
from api import service

router = APIRouter()


def _to_hotel_items(raw: list[dict]) -> list[HotelItem]:
    items = []
    for h in raw:
        items.append(HotelItem(
            name=h.get("name"),
            city=h.get("city"),
            country=h.get("country"),
            price=h.get("price") or h.get("price_per_night"),
            rating=h.get("rating"),
            url=h.get("url"),
            map_url=h.get("map_url"),
            photo_url=h.get("photo_url"),
        ))
    return items


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health():
    return HealthResponse()


@router.post("/search", response_model=SearchResponse, tags=["travel"])
async def search(req: SearchRequest):
    """Run the full travel workflow: weather and hotels."""
    try:
        result = await service.search(
            origin=req.origin,
            destination=req.destination,
            start_date=req.start_date,
            end_date=req.end_date,
            bedrooms=req.bedrooms,
            max_price=req.max_price_per_night,
            min_rating=req.min_rating,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SearchResponse(
        origin=result.get("origin"),
        destination=result.get("destination"),
        start_date=result.get("start_date"),
        end_date=result.get("end_date"),
        weather_summary=result.get("weather_summary"),
        recommended_hotels=_to_hotel_items(result.get("recommended_hotels") or []),
    )
