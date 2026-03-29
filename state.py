from typing import TypedDict, List, Optional, Annotated
import operator


class ContentState(TypedDict):
    # ── Input ──────────────────────────────────────────────
    input_type: str          # PRODUCT_SPEC | COMPLIANCE_CHECK | ENGAGEMENT_DATA
    raw_input: str

    # ── Research ───────────────────────────────────────────
    research_brief: str      # JSON string: {VERIFIED_FACTS, UNVERIFIED_CLAIMS, KEY_CONTEXT}

    # ── Drafts ─────────────────────────────────────────────
    blog_post: str
    social_posts: dict       # {linkedin, twitter, instagram}
    faq: str

    # ── Review ─────────────────────────────────────────────
    review_status: str       # PENDING | PASS | FAIL
    violations: List[dict]   # [{sentence, rule, severity, rewrite_suggestion}]
    retry_count: int
    confidence_scores: dict  # {stat_or_claim: verified|unverified|blocked}

    # ── Human gate ─────────────────────────────────────────
    human_approved: bool
    human_feedback: str

    # ── Localization ───────────────────────────────────────
    hindi_content: str
    tamil_content: str

    # ── Strategy (Performance Pivot) ───────────────────────
    content_calendar: str
    strategy_recommendation: str

    # ── Audit trail ────────────────────────────────────────
    audit_log: Annotated[List[dict], operator.add]
    pipeline_start_time: str
    completed_at: str

    published_assets: list  # add this line to ContentState


def initial_state(input_type: str, raw_input: str) -> ContentState:
    from datetime import datetime
    return ContentState(
        input_type=input_type,
        raw_input=raw_input,
        research_brief="",
        blog_post="",
        social_posts={},
        faq="",
        review_status="PENDING",
        violations=[],
        retry_count=0,
        confidence_scores={},
        human_approved=False,
        human_feedback="",
        hindi_content="",
        tamil_content="",
        content_calendar="",
        strategy_recommendation="",
        audit_log=[],
        pipeline_start_time=datetime.now().isoformat(),
        completed_at="",
    )
