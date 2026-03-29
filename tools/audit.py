from datetime import datetime
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def log_decision(state: dict, agent: str, decision: str, reasoning: str) -> dict:
    """Append a structured entry to audit_log and pretty-print to console."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "decision": decision,
        "reasoning": reasoning,
        "retry_count": state.get("retry_count", 0),
    }
    # Rich console output so you can watch the pipeline live
    color_map = {
        "supervisor": "bold cyan",
        "researcher": "bold blue",
        "drafter": "bold yellow",
        "reviewer": "bold magenta",
        "localizer": "bold green",
        "strategy": "bold green",
        "human_gate": "bold white",
    }
    color = color_map.get(agent, "white")
    console.print(
        Panel(
            f"[{color}]{agent.upper()}[/{color}]  →  {decision}\n"
            f"[dim]{reasoning}[/dim]",
            title=f"[dim]{entry['timestamp']}[/dim]",
            border_style="dim",
        )
    )
    # Return the entry to be added via Annotated[List, operator.add]
    return entry
