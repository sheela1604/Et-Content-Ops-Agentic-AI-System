from asyncio import graph
from langgraph.graph import StateGraph, END
from agents.publisher import publisher_agent
from state import ContentState
from agents import (
    supervisor_node, route_from_supervisor,
    researcher_node,
    drafter_node,
    reviewer_node, route_from_reviewer,
    human_gate_node, route_from_human,
    localizer_node,
    strategy_node,
)


def build_graph() -> StateGraph:
    graph = StateGraph(ContentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("supervisor",  supervisor_node)
    graph.add_node("researcher",  researcher_node)
    graph.add_node("drafter",     drafter_node)
    graph.add_node("reviewer",    reviewer_node)
    graph.add_node("human_gate",  human_gate_node)
    graph.add_node("localizer",   localizer_node)
    graph.add_node("strategy",    strategy_node)
    graph.add_node("publisher", publisher_agent)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("supervisor")

    # ── Conditional: supervisor → researcher | reviewer | strategy ────────────
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "researcher": "researcher",
            "reviewer":   "reviewer",
            "strategy":   "strategy",
        },
    )

    # ── Linear: researcher → drafter ─────────────────────────────────────────
    graph.add_edge("researcher", "drafter")

    # ── Linear: drafter → reviewer ───────────────────────────────────────────
    graph.add_edge("drafter", "reviewer")

    # ── Conditional: reviewer → drafter (retry) | human_gate (pass/escalate) ─
    graph.add_conditional_edges(
        "reviewer",
        route_from_reviewer,
        {
            "drafter":    "drafter",
            "human_gate": "human_gate",
        },
    )

    # ── Conditional: human_gate → localizer (approved) | drafter (feedback) ──
    graph.add_conditional_edges(
        "human_gate",
        route_from_human,
        {
            "localizer": "localizer",
            "drafter":   "drafter",
        },
    )

    # ── Terminals ─────────────────────────────────────────────────────────────
    graph.add_edge("localizer", "publisher")
    graph.add_edge("publisher", END)
    graph.add_edge("strategy",  END)

    return graph.compile()


# Singleton — import this in main.py and run scripts
app = build_graph()
