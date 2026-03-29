"""
Benchmark: run all 3 judge scenarios and compare agent time vs manual estimate.
Prints a clean before/after table for the demo impact quantification slide.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DEMO_AUTO_APPROVE"] = "true"

from rich.console import Console
from rich.table import Table
from rich import box
from state import initial_state
from graph import app
from scenarios.inputs import (
    PRODUCT_LAUNCH_SPEC,
    COMPLIANCE_CHECK_SAMPLE,
    ENGAGEMENT_DATA_SAMPLE,
)

console = Console()

SCENARIOS = [
    ("Product Launch Sprint",   "PRODUCT_SPEC",     PRODUCT_LAUNCH_SPEC,    240),  # 4h manual
    ("Compliance Rejection",    "COMPLIANCE_CHECK", COMPLIANCE_CHECK_SAMPLE,  30),  # 30min manual
    ("Performance Pivot",       "ENGAGEMENT_DATA",  ENGAGEMENT_DATA_SAMPLE,   60),  # 1h manual
]

results = []

console.print("\n[bold cyan]ET Content Ops — Benchmark[/bold cyan]\n")

for name, itype, raw, manual_mins in SCENARIOS:
    console.print(f"[dim]Running: {name}...[/dim]")
    state = initial_state(itype, raw)
    t0 = time.perf_counter()
    final = app.invoke(state)
    elapsed = round(time.perf_counter() - t0, 1)
    speedup = round((manual_mins * 60) / elapsed, 1)
    results.append((name, elapsed, manual_mins * 60, speedup, final.get("review_status","?")))

t = Table(title="Impact Quantification", box=box.ROUNDED, show_lines=True)
t.add_column("Scenario",         style="bold")
t.add_column("Agent time",       justify="right", style="cyan")
t.add_column("Manual estimate",  justify="right", style="dim")
t.add_column("Speedup",          justify="right", style="bold green")
t.add_column("Review status",    justify="center")

for name, agent_s, manual_s, speedup, status in results:
    status_fmt = f"[green]{status}[/green]" if status == "PASS" else f"[red]{status}[/red]"
    t.add_row(
        name,
        f"{agent_s}s",
        f"{manual_s//60}m",
        f"{speedup}×",
        status_fmt,
    )

console.print(t)
total_manual = sum(r[2] for r in results)
total_agent  = sum(r[1] for r in results)
console.print(f"\nTotal: [cyan]{total_agent:.1f}s[/cyan] agent vs [dim]{total_manual//60} min[/dim] manual → [bold green]{round(total_manual/total_agent, 1)}× overall speedup[/bold green]\n")

# Save for demo slides
os.makedirs("outputs", exist_ok=True)
with open("outputs/benchmark.json", "w") as f:
    json.dump([{"scenario": r[0], "agent_s": r[1], "manual_s": r[2], "speedup": r[3], "status": r[4]} for r in results], f, indent=2)
console.print("[dim]Saved → outputs/benchmark.json[/dim]\n")
