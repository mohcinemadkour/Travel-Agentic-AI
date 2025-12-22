"""A minimal, local replacement for the small pieces of `langgraph` used by this repo.

This implements a tiny `StateGraph` with the limited API the project needs:
- add_node(name, func)
- add_edge(from, to)
- add_conditional_edges(node, route_fn, mapping)
- set_entry_point(name)
- compile() -> returns an object with `invoke(state)`

This is intentionally simple and synchronous; it exists so the deployed image doesn't fail
when the external `langgraph` package is not available.
"""
from typing import Callable, Dict, Any, Optional


# Sentinel for graph end
END = "__END__"


class CompiledGraph:
    def __init__(self, nodes, edges, conditional_edges, entry_point, state_type=None):
        self._nodes = nodes
        self._edges = edges
        self._conditional = conditional_edges
        self._entry = entry_point
        self._state_type = state_type

    def invoke(self, state: Any):
        current = self._entry
        ctx = state

        while current is not None and current != END:
            func = self._nodes.get(current)
            if func is None:
                break

            # Call node function; allow it to mutate or return a new state
            try:
                result = func(ctx)
            except TypeError:
                # Some functions may expect no args — call without
                result = func()

            if result is not None:
                ctx = result

            # Conditional routing
            if current in self._conditional:
                route_fn, mapping = self._conditional[current]
                try:
                    target = route_fn(ctx)
                except Exception:
                    target = None

                # mapping may already contain node names; if not found, stop
                current = mapping.get(target)
                continue

            # Deterministic single edge
            next_nodes = self._edges.get(current, [])
            if not next_nodes:
                break
            # follow first edge by default
            current = next_nodes[0]

        return ctx


class StateGraph:
    def __init__(self, state_type=None):
        self._state_type = state_type
        self._nodes: Dict[str, Callable] = {}
        self._edges: Dict[str, list] = {}
        self._conditional: Dict[str, tuple] = {}
        self._entry: Optional[str] = None

    def add_node(self, name: str, func: Callable):
        self._nodes[name] = func

    def add_edge(self, src: str, dst: str):
        self._edges.setdefault(src, []).append(dst)

    def add_conditional_edges(self, node: str, route_fn: Callable, mapping: Dict[str, str]):
        self._conditional[node] = (route_fn, mapping)

    def set_entry_point(self, name: str):
        self._entry = name

    def compile(self):
        return CompiledGraph(self._nodes, self._edges, self._conditional, self._entry, self._state_type)
