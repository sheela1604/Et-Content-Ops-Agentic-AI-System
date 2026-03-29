import json
from state import ContentState
from config import get_small_llm, call_llm_json
from tools import check_rules, has_hard_blocks, violations_to_dict, check_facts, get_hallucination_risks, log_decision

LLM_REVIEW_PROMPT = """You are a compliance reviewer for Economic Times.

Review the content below for:
1. Misleading implication (technically true but creates false impression)
2. Overpromising language (implies certainty where none exists)
3. Missing required disclaimers for financial/investment content
4. Claims inconsistent with the research brief

Research brief (VERIFIED_FACTS only):
{verified_facts}

Content to review:
{content}

Respond with ONLY this JSON (no markdown, no preamble):
{{
  "verdict": "PASS" or "FAIL",
  "violations": [
    {{
      "sentence": "exact sentence from content",
      "rule": "SEBI | IRDAI | ET-BRAND | FACTUAL",
      "description": "what is wrong",
      "severity": "BLOCK" or "FLAG",
      "rewrite_suggestion": "compliant rewrite of that sentence"
    }}
  ],
  "confidence_note": "one sentence summary of overall compliance status"
}}
If verdict is PASS, violations array must be empty.
"""


def reviewer_node(state: ContentState) -> ContentState:
    small_llm = get_small_llm(temperature=0.0)
    if state.get("retry_count", 0) >= 3:
        entry = log_decision(state, "reviewer", "PASS", "Force-passed after max retries")
        return {**state, "review_status": "PASS", "violations": [], "audit_log": [entry]}

    small_llm = get_small_llm(temperature=0.0)

    # Determine what to review — blog post for PRODUCT_SPEC, raw_input for COMPLIANCE_CHECK
    if state["input_type"] == "COMPLIANCE_CHECK":
        content = state["raw_input"]
    else:
        content = state.get("blog_post", "")

    if not content.strip():
        entry = log_decision(state, "reviewer", "SKIP", "No content to review")
        return {**state, "review_status": "PASS", "audit_log": [entry]}

    # ── Layer 3: Deterministic rule check (fast, no LLM) ─────────────────────
    rule_violations = check_rules(content)
    blocks = [v for v in rule_violations if v.severity == "BLOCK"]
    flags  = [v for v in rule_violations if v.severity == "FLAG"]

    if blocks:
        entry = log_decision(
            state, "reviewer", "FAIL — HARD BLOCK",
            f"Rule {blocks[0].rule_id}: {blocks[0].description}"
        )
        return {
            **state,
            "review_status": "FAIL",
            "violations": violations_to_dict(blocks + flags),
            "retry_count": state["retry_count"] + 1,
            "audit_log": [entry],
        }

    # ── Layer 4a: Fact-check stats against research brief ────────────────────
    fact_scores = check_facts(content, state.get("research_brief", ""))
    hallucinated = get_hallucination_risks(fact_scores)

    if hallucinated:
        viol = [{
            "sentence": f"Unverified statistic in content: '{s}'",
            "rule": "FACTUAL-001",
            "severity": "BLOCK",
            "description": "Statistic not found in research brief — possible hallucination",
            "rewrite_suggestion": "Remove statistic or verify against a named source and add to research brief",
        } for s in hallucinated[:3]]   # cap at 3 to avoid noise
        entry = log_decision(
            state, "reviewer", "FAIL — UNVERIFIED STATS",
            f"Found {len(hallucinated)} unverified statistic(s): {hallucinated[:3]}"
        )
        return {
            **state,
            "review_status": "FAIL",
            "violations": viol,
            "confidence_scores": fact_scores,
            "retry_count": state["retry_count"] + 1,
            "audit_log": [entry],
        }

    # ── Layer 4b: LLM semantic review (nuanced cases) ────────────────────────
    try:
        brief = json.loads(state.get("research_brief", "{}"))
    except (json.JSONDecodeError, TypeError):
        brief = {}

    verified_facts_text = json.dumps(brief.get("VERIFIED_FACTS", []), indent=2)

    llm_prompt = LLM_REVIEW_PROMPT.format(
        verified_facts=verified_facts_text[:1500],
        content=content[:2000],
    )
    raw = call_llm_json(small_llm, llm_prompt, label="reviewer-semantic")
    clean = raw.strip().strip("```json").strip("```").strip()

    try:
        result = json.loads(clean)
        verdict = result.get("verdict", "PASS").upper()
        llm_violations = result.get("violations", [])
        confidence_note = result.get("confidence_note", "")
    except (json.JSONDecodeError, KeyError):
        verdict = "PASS"
        llm_violations = []
        confidence_note = "LLM review parse error — defaulting to PASS"

    # Merge FLAG violations from Layer 3 into LLM result
    all_violations = llm_violations + violations_to_dict(flags)

    if verdict == "FAIL":
        entry = log_decision(
            state, "reviewer", "FAIL — SEMANTIC",
            f"LLM found {len(llm_violations)} issue(s). {confidence_note}"
        )
        return {
            **state,
            "review_status": "FAIL",
            "violations": all_violations,
            "confidence_scores": fact_scores,
            "retry_count": state["retry_count"] + 1,
            "audit_log": [entry],
        }

    entry = log_decision(
        state, "reviewer", "PASS",
        f"{confidence_note} | Flags noted: {len(flags)}"
    )
    return {
        **state,
        "review_status": "PASS",
        "violations": all_violations,   # pass flags through for human to see
        "confidence_scores": fact_scores,
        "audit_log": [entry],
    }
