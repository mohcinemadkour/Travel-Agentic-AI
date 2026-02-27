from pydantic import BaseModel
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END

class MyState(BaseModel):
    items: List[int] = []

def node1(state):
    state.items = [1, 2, 3]
    return state

def node2(state):
    state.items = state.items[:2]
    return state

graph = StateGraph(MyState)
graph.add_node("n1", node1)
graph.add_node("n2", node2)
graph.set_entry_point("n1")
graph.add_edge("n1", "n2")
graph.add_edge("n2", END)

app = graph.compile()
print(app.invoke(MyState()))
