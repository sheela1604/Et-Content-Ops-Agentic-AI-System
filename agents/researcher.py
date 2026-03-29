import json
from state import ContentState
from config import get_large_llm, call_llm_json
from tools import fetch_rss_context, extract_keywords_from_spec, log_decision

RESEARCH_PROMPT = """You are a research agent for Economic Times content operations.

Given a product spec, extract and structure facts for the content team.
Use ONLY the provided source material — do NOT invent statistics.

Product spec:
{product_spec}

Related news context (from ET RSS):
{rss_context}

Respond with ONLY this JSON (no markdown, no preamble):
{{
  "VERIFIED_FACTS": [
    {{"claim": "exact factual claim", "source": "product spec or ET RSS", "date": "if available"}}
  ],
  "UNVERIFIED_CLAIMS": [
    {{"claim": "claim that needs verification", "reason_unverified": "why it cannot be confirmed"}}
  ],
  "KEY_CONTEXT": "2-3 sentence summary of the product and market context for the Drafter",
  "TARGET_AUDIENCE": "who this content is for",
  "KEY_MESSAGES": ["top message 1", "top message 2", "top message 3"]
}}
"""


def researcher_node(state: ContentState) -> ContentState:
    llm = get_large_llm(temperature=0.2)

    # 1. Extract keywords from spec for RSS lookup
    keywords = extract_keywords_from_spec(state["raw_input"])

    # 2. Fetch related ET news
    rss_items = fetch_rss_context(keywords, max_items=4)
    rss_context = "\n".join(
        f"- {item.get('title','')}: {item.get('summary','')}"
        for item in rss_items
        if "error" not in item
    ) or "No related news found."

    # 3. Build research brief via LLM
    prompt = RESEARCH_PROMPT.format(
        product_spec=state["raw_input"],
        rss_context=rss_context,
    )
    raw = call_llm_json(llm, prompt, label="researcher-brief")
    clean = raw.strip().strip("```json").strip("```").strip()

    # Validate JSON — fall back to minimal structure on parse error
    try:
        json.loads(clean)
        brief = clean
    except json.JSONDecodeError:
        brief = json.dumps({
            "VERIFIED_FACTS": [{"claim": state["raw_input"][:300], "source": "product spec", "date": ""}],
            "UNVERIFIED_CLAIMS": [],
            "KEY_CONTEXT": state["raw_input"][:200],
            "TARGET_AUDIENCE": "general investors",
            "KEY_MESSAGES": ["Product details as provided in spec"],
        })

    entry = log_decision(
        state, "researcher", "BRIEF READY",
        f"Fetched {len(rss_items)} RSS items, extracted {len(keywords)} keywords"
    )
    return {**state, "research_brief": brief, "audit_log": [entry]}
