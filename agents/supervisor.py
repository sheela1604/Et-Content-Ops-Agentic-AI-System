import json
from state import ContentState
from config import get_small_llm, call_llm_json
from tools import log_decision

CLASSIFY_PROMPT = """You are an input classifier for a content operations pipeline.

Classify the following input into EXACTLY one of these types:
- PRODUCT_SPEC   : a product description, spec sheet, or launch brief
- COMPLIANCE_CHECK : a piece of content that needs compliance review
- ENGAGEMENT_DATA  : analytics data, performance metrics, or engagement statistics

Input:
{raw_input}

Respond with ONLY a JSON object, no other text:
{{"input_type": "PRODUCT_SPEC"|"COMPLIANCE_CHECK"|"ENGAGEMENT_DATA", "reasoning": "one sentence"}}
"""


def supervisor_node(state: ContentState) -> ContentState:
    llm = get_small_llm(temperature=0.0)

    prompt = CLASSIFY_PROMPT.format(raw_input=state["raw_input"][:1000])
    raw = call_llm_json(llm, prompt, label="supervisor-classify")

    # Parse JSON — strip markdown fences if model adds them
    clean = raw.strip().strip("```json").strip("```").strip()
    try:
        result = json.loads(clean)
        input_type = result.get("input_type", "PRODUCT_SPEC")
        reasoning = result.get("reasoning", "Classified by LLM")
    except (json.JSONDecodeError, KeyError):
        # Fallback: look for keywords in raw text
        raw_up = raw.upper()
        if "COMPLIANCE" in raw_up:
            input_type, reasoning = "COMPLIANCE_CHECK", "Keyword fallback: COMPLIANCE detected"
        elif "ENGAGEMENT" in raw_up or "ANALYTICS" in raw_up:
            input_type, reasoning = "ENGAGEMENT_DATA", "Keyword fallback: ENGAGEMENT detected"
        else:
            input_type, reasoning = "PRODUCT_SPEC", "Keyword fallback: defaulting to PRODUCT_SPEC"

    entry = log_decision(state, "supervisor", f"ROUTE → {input_type}", reasoning)
    return {**state, "input_type": input_type, "audit_log": [entry]}


# ── Conditional edge functions ────────────────────────────────────────────────

def route_from_supervisor(state: ContentState) -> str:
    t = state["input_type"]
    if t == "COMPLIANCE_CHECK":
        return "reviewer"
    if t == "ENGAGEMENT_DATA":
        return "strategy"
    return "researcher"   # PRODUCT_SPEC default


def route_from_reviewer(state: ContentState) -> str:
    if state["review_status"] == "PASS":
        return "human_gate"
    if state["retry_count"] >= 2:
        return "human_gate"   # escalate after 2 retries
    return "drafter"          # loop back with feedback


def route_from_human(state: ContentState) -> str:
    if state["human_approved"]:
        return "localizer"
    return "drafter"          # incorporate human feedback
