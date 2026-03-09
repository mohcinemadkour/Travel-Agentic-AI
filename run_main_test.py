"""Non-interactive test runner for main.py

This script mocks `TravelState` and `build_graph` inside the imported
`main` module so we can exercise the CLI flow without network calls.
"""
from types import SimpleNamespace
import sys
import types

class DummyState:
    def __init__(self, **kwargs):
        self._data = kwargs
    def model_dump(self):
        return self._data

class FakeGraph:
    def invoke(self, state):
        return {
            "weather_summary": "Clear skies for the selected dates.",
            "recommended_hotels": [
                {"name": "Test Hotel", "rating": 4.5, "price": 120, "url": "https://example.com/hotel/1"}
            ],
        }

fake_graph_mod = types.SimpleNamespace(build_graph=lambda: FakeGraph())
fake_state_mod = types.SimpleNamespace(TravelState=DummyState)
sys.modules["graph"] = fake_graph_mod
sys.modules["state"] = fake_state_mod

import importlib
main = importlib.import_module("main")

inputs = iter([
    "BLR",        # Origin
    "BOM",        # Destination
    "2026-01-10", # Start date
    "2026-01-15", # End date
    "1",          # Bedrooms
    "150",        # Max price
    "4.2",        # Min rating
])

import builtins
real_input = builtins.input
builtins.input = lambda prompt='': next(inputs)

try:
    main.main()
finally:
    builtins.input = real_input
