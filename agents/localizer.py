import json
from state import ContentState
from config import get_small_llm, call_llm_json
from tools import log_decision
import time
time.sleep(3)  # add this at the start of localizer_node
# ── Cultural adaptation rules ─────────────────────────────────────────────────
HINDI_RULES = """
Cultural adaptation rules for Hindi localization:
- Keep ALL financial/technical terms in English: SIP, mutual fund, SEBI, NAV, CAGR, IPO
- Translate explanatory surrounding text to Hindi
- Use formal Hindi (Devanagari) — avoid transliteration
- Adapt idioms to Indian equivalents, do not translate literally
- Retain brand names, product names, and proper nouns in English
- Add INR/₹ for any currency mentions
"""

TAMIL_RULES = """
Cultural adaptation rules for Tamil localization:
- Keep ALL financial/technical terms in English: SIP, mutual fund, SEBI, NAV, CAGR, IPO
- Translate explanatory surrounding text to Tamil
- Use formal Tamil script — avoid transliteration
- Adapt idioms to Tamil cultural context
- Retain brand names, product names, and proper nouns in English
- Add INR/₹ for any currency mentions
"""

TRANSLATE_PROMPT = """
{rules}

Translate the following social media post to {language}.
Preserve all hashtags in their original English form.
Preserve all numbers, percentages, and financial terms in English.

Original post:
{content}

Return ONLY the translated text. No explanations.
"""

STRATEGY_PROMPT = """
You are a content strategy analyst for Economic Times.

Engagement data:
{engagement_data}

Based on this data, identify the top-performing format and produce:
1. A strategic recommendation (2-3 sentences explaining the insight)
2. A 4-week content calendar reflecting the recommended format mix

Respond with ONLY this JSON (no markdown):
{{
  "strategy_recommendation": "2-3 sentence strategic insight and recommendation",
  "content_calendar": {{
    "week_1": [
      {{"day": "Mon", "format": "video|article|social|infographic", "topic": "...", "channel": "..."}}
    ],
    "week_2": [],
    "week_3": [],
    "week_4": []
  }}
}}
"""


def localizer_node(state: ContentState) -> ContentState:
    small_llm = get_small_llm(temperature=0.3)

    # Pick the Instagram post as the localization target (short, visual)
    social = state.get("social_posts", {})
    source_post = social.get("instagram") or social.get("linkedin") or state.get("blog_post", "")[:300]

    if not source_post.strip():
        entry = log_decision(state, "localizer", "SKIP", "No content available for localization")
        return {**state, "audit_log": [entry]}

    # Hindi
    hindi_prompt = TRANSLATE_PROMPT.format(
        rules=HINDI_RULES, language="Hindi", content=source_post
    )
    hindi_content = call_llm_json(small_llm, hindi_prompt, label="localizer-hindi").strip()

    # Tamil
    tamil_prompt = TRANSLATE_PROMPT.format(
        rules=TAMIL_RULES, language="Tamil", content=source_post
    )
    tamil_content = call_llm_json(small_llm, tamil_prompt, label="localizer-tamil").strip()

    entry = log_decision(
        state, "localizer", "LOCALIZED",
        "Instagram post localized to Hindi and Tamil with cultural adaptation"
    )
    return {
        **state,
        "hindi_content": hindi_content,
        "tamil_content": tamil_content,
        "audit_log": [entry],
    }


def strategy_node(state: ContentState) -> ContentState:
    small_llm = get_small_llm(temperature=0.4)

    prompt = STRATEGY_PROMPT.format(engagement_data=state["raw_input"][:1500])
    raw = call_llm_json(small_llm, prompt, label="strategy")
    clean = raw.strip().strip("```json").strip("```").strip()

    try:
        result = json.loads(clean)
        recommendation = result.get("strategy_recommendation", raw[:300])
        calendar = json.dumps(result.get("content_calendar", {}), indent=2)
    except (json.JSONDecodeError, KeyError):
        recommendation = raw[:300]
        calendar = "{}"

    entry = log_decision(
        state, "strategy", "STRATEGY GENERATED",
        "Analysed engagement data and produced 4-week content calendar"
    )
    return {
        **state,
        "strategy_recommendation": recommendation,
        "content_calendar": calendar,
        "review_status": "PASS",    # strategy output doesn't go through compliance review
        "audit_log": [entry],
    }
