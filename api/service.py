"""
Business logic layer — bridges the API endpoints to the LangGraph workflow.
Runs blocking graph calls in a thread pool so FastAPI stays async.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from state import TravelState
from graph import build_graph

_executor = ThreadPoolExecutor(max_workers=4)


def _run_sync(fn, *args, **kwargs):
    """Run a blocking function in the thread pool, return an awaitable."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, partial(fn, *args, **kwargs))


def _invoke_graph(origin, destination, start_date, end_date, bedrooms, max_price, min_rating) -> dict:
    graph = build_graph()
    initial_state = TravelState(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        bedrooms=bedrooms,
        max_price_per_night=max_price,
        min_rating=min_rating,
    )
    result = graph.invoke(initial_state)
    if isinstance(result, TravelState):
        return result.model_dump()
    return result


async def search(origin, destination, start_date, end_date, bedrooms, max_price, min_rating) -> dict:
    return await _run_sync(
        _invoke_graph, origin, destination, start_date, end_date,
        bedrooms, max_price, min_rating,
    )
