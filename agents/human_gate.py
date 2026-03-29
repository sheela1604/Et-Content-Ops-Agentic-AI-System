from state import ContentState
from tools import log_decision
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import json

console = Console()


def human_gate_node(state: ContentState) -> ContentState:
    """
    Presents the full draft and audit trail to a human editor.
    In demo mode: auto-approves if review_status is PASS, else asks for input.
    Set DEMO_AUTO_APPROVE=true in .env to skip interactive prompt entirely.
    """
    import os
    auto_approve = os.getenv("DEMO_AUTO_APPROVE", "false").lower() == "true"
    if state.get("retry_count", 0) >= 3:
        entry = log_decision(state, "human_gate", "APPROVED", "Force-approved after max retries — stopping loop")
        return {**state, "human_approved": True, "human_feedback": "Force-approved", "audit_log": [entry]}
    
    _print_review_summary(state)

    if auto_approve:
        approved = state["review_status"] == "PASS"
        feedback = "Auto-approved (DEMO_AUTO_APPROVE=true)" if approved else "Auto-rejected: review failures present"
        entry = log_decision(
            state, "human_gate",
            "APPROVED" if approved else "REJECTED",
            feedback
        )
        return {**state, "human_approved": approved, "human_feedback": feedback, "audit_log": [entry]}

    # Interactive mode
    console.print("\n[bold]Human editor review required.[/bold]")
    console.print(f"Review status from agents: [{'green' if state['review_status'] == 'PASS' else 'red'}]{state['review_status']}[/]")

    if state["retry_count"] >= 2 and state["review_status"] == "FAIL":
        console.print("[yellow]⚠ Max auto-retries reached. Escalated to human.[/yellow]")

    decision = ""
    while decision not in ("y", "n", "yes", "no"):
        decision = console.input("\nApprove content for localization and publishing? [y/n]: ").strip().lower()
    approved = decision in ("y", "yes")
    feedback = ""
    if not approved:
        feedback = console.input("Enter feedback for the Drafter: ").strip()

    entry = log_decision(
        state, "human_gate",
        "APPROVED" if approved else f"REJECTED — {feedback[:60]}",
        "Human editorial decision"
    )
    return {
        **state,
        "human_approved": approved,
        "human_feedback": feedback,
        "audit_log": [entry],
    }


def _print_review_summary(state: ContentState):
    console.print(Panel("[bold cyan]HUMAN GATE — Editorial Review[/bold cyan]", border_style="cyan"))

    # Blog excerpt
    blog = state.get("blog_post", "")
    if blog:
        console.print(Panel(blog[:600] + "...", title="Blog post (excerpt)", border_style="dim"))

    # Violations table
    violations = state.get("violations", [])
    if violations:
        t = Table(title="Compliance flags", box=box.SIMPLE_HEAVY)
        t.add_column("Rule", style="yellow")
        t.add_column("Severity", style="red")
        t.add_column("Sentence")
        t.add_column("Suggested fix", style="green")
        for v in violations:
            t.add_row(
                v.get("rule", ""),
                v.get("severity", ""),
                v.get("sentence", "")[:60],
                v.get("rewrite_suggestion", "")[:60],
            )
        console.print(t)

    # Confidence scores
    scores = state.get("confidence_scores", {})
    if scores:
        console.print(f"\n[dim]Fact confidence scores: {scores}[/dim]")

    # Audit log summary
    console.print(f"\n[dim]Pipeline steps so far: {len(state.get('audit_log', []))} | Retries: {state.get('retry_count', 0)}[/dim]")
