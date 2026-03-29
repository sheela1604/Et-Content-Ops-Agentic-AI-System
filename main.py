import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

load_dotenv()

from state import initial_state
from graph import app
from scenarios.inputs import (
    PRODUCT_LAUNCH_SPEC,
    COMPLIANCE_CHECK_SAMPLE,
    ENGAGEMENT_DATA_SAMPLE,
)




console = Console()

SCENARIOS = {
    "1": ("Product Launch Sprint",    "PRODUCT_SPEC",     PRODUCT_LAUNCH_SPEC),
    "2": ("Compliance Rejection",     "COMPLIANCE_CHECK", COMPLIANCE_CHECK_SAMPLE),
    "3": ("Performance Pivot",        "ENGAGEMENT_DATA",  ENGAGEMENT_DATA_SAMPLE),
}


def run_scenario(name: str, input_type: str, raw_input: str) -> dict:
    console.print(Panel(
        f"[bold white]{name}[/bold white]\n[dim]Input type: {input_type}[/dim]",
        title="[bold cyan]RUNNING SCENARIO[/bold cyan]",
        border_style="cyan",
    ))

    start = time.perf_counter()
    state = initial_state(input_type, raw_input)

    # Stream the graph — each node update is printed by the agents themselves
    final_state = app.invoke(state)

    elapsed = time.perf_counter() - start
    final_state["completed_at"] = datetime.now().isoformat()

    _print_results(name, final_state, elapsed)
    _save_outputs(name, final_state)

    return final_state


def _print_results(name: str, state: dict, elapsed: float):
    console.rule(f"[bold green]RESULTS — {name}[/bold green]")

    # Summary table
    t = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    t.add_column("Field", style="dim", width=22)
    t.add_column("Value")

    t.add_row("Elapsed time",    f"{elapsed:.1f}s")
    t.add_row("Review status",   f"[green]{state.get('review_status','')}[/green]" if state.get("review_status") == "PASS" else f"[red]{state.get('review_status','')}[/red]")
    t.add_row("Retries used",    str(state.get("retry_count", 0)))
    t.add_row("Human approved",  str(state.get("human_approved", False)))
    t.add_row("Audit entries",   str(len(state.get("audit_log", []))))
    t.add_row("Violations",      str(len(state.get("violations", []))))
    console.print(t)

    # Content assets
    if state.get("blog_post"):
        console.print(Panel(
            state["blog_post"][:800] + ("..." if len(state["blog_post"]) > 800 else ""),
            title="Blog post", border_style="blue"
        ))

    social = state.get("social_posts", {})
    if social:
        for platform, post in social.items():
            console.print(Panel(str(post)[:300], title=f"Social — {platform}", border_style="dim"))

    if state.get("hindi_content"):
        console.print(Panel(state["hindi_content"][:300], title="Hindi localization", border_style="green"))

    if state.get("tamil_content"):
        console.print(Panel(state["tamil_content"][:300], title="Tamil localization", border_style="green"))

    if state.get("strategy_recommendation"):
        console.print(Panel(state["strategy_recommendation"], title="Strategy recommendation", border_style="yellow"))

    if state.get("content_calendar"):
        try:
            cal = json.loads(state["content_calendar"])
            console.print(Panel(json.dumps(cal, indent=2)[:600], title="4-week content calendar", border_style="yellow"))
        except Exception:
            console.print(Panel(state["content_calendar"][:400], title="Content calendar", border_style="yellow"))

    # Audit trail
    console.rule("[dim]Audit trail[/dim]")
    for entry in state.get("audit_log", []):
        console.print(
            f"  [dim]{entry.get('timestamp','')[:19]}[/dim]  "
            f"[bold]{entry.get('agent','').upper():12}[/bold]  "
            f"{entry.get('decision','')}"
        )


def _save_outputs(name: str, state: dict):
    os.makedirs("outputs", exist_ok=True)
    slug = name.lower().replace(" ", "_")
    path = f"outputs/{slug}_{datetime.now().strftime('%H%M%S')}.json"

    # Serialise — state may contain non-JSON-serialisable objects
    out = {k: (v if isinstance(v, (str, int, float, bool, list, dict, type(None))) else str(v))
           for k, v in state.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    console.print(f"\n[dim]Output saved → {path}[/dim]")


def main():
    console.print(Panel(
        "[bold]ET GenAI Hackathon 2026[/bold]\n"
        "Track 1: AI for Enterprise Content Operations\n"
        "[dim]Powered by LangGraph + Ollama[/dim]",
        border_style="cyan",
    ))

    console.print("\nSelect scenario to run:")
    for k, (name, _, _) in SCENARIOS.items():
        console.print(f"  [{k}] {name}")
    console.print("  [a] Run all three scenarios")

    choice = input("\nYour choice: ").strip().lower()

    if choice == "a":
        for k, (name, input_type, raw_input) in SCENARIOS.items():
            run_scenario(name, input_type, raw_input)
            console.print()
    elif choice in SCENARIOS:
        name, input_type, raw_input = SCENARIOS[choice]
        run_scenario(name, input_type, raw_input)
    else:
        console.print("[red]Invalid choice.[/red]")


if __name__ == "__main__":
    main()
