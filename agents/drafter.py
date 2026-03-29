import json
from state import ContentState
from config import get_large_llm, get_small_llm, call_llm_json
from tools import log_decision
import re

def strip_unverified_stats(sentence, verified_stats):
    # Remove any percentage not in verified stats
    percentages = re.findall(r'\d+(?:\.\d+)?%', sentence)
    for pct in percentages:
        if pct not in verified_stats:
            # Replace the whole stat range e.g "20-105%" too
            sentence = re.sub(r'\d+(?:\.\d+)?[-–]?' + re.escape(pct), '', sentence)
            sentence = re.sub(r'\s+', ' ', sentence).strip()
    return sentence
# ── ET Style Constitution ─────────────────────────────────────────────────────
ET_STYLE_CONSTITUTION = """
ECONOMIC TIMES CONTENT STANDARDS — MANDATORY COMPLIANCE

ANTI-HALLUCINATION RULES (MANDATORY):
- ONLY use statistics that appear VERBATIM in the research brief
- If a number is not in the research brief, DO NOT write it — describe qualitatively instead
- NEVER invent percentage ranges, return figures, or financial stats
- NEVER paraphrase or estimate statistics (e.g. do not round 6.5-7.2% to "around 7%")
- When in doubt, leave the number out

FORBIDDEN PHRASES (never use):
- "guaranteed returns", "assured returns", "risk-free", "zero risk"
- "will definitely", "100% accurate", "no risk", "double your money"
- "best in class", "number one" (unless citing a source)
- "revolutionary" (overused), "game-changer" (overused)

COMPLIANCE RULES:
- Only cite statistics that appear in the VERIFIED_FACTS section
- For any investment product mention: include disclaimer
  "Consult a SEBI-registered investment advisor before investing."
- Never state future performance as fact — use "historically" or "as of [date]"
- Every numeric claim must reference its source

ET TONE RULES:
- Authoritative but accessible — explain jargon on first use
- Active voice preferred over passive
- Lead with the news angle, not background
- Headlines: max 10 words, present tense, no clickbait
- Paragraphs: max 3 sentences each
"""

BLOG_PROMPT = """
{constitution}

Research brief (use ONLY VERIFIED_FACTS for claims):
{research_brief}

{feedback_section}

Write a 400-500 word blog post for Economic Times. Structure:
1. Headline (max 10 words)
2. Opening paragraph (news angle)
3. 2-3 body sections with subheadings
4. Closing with CTA
5. Disclaimer if investment-related

Return ONLY the blog post text.
"""

SOCIAL_PROMPT = """
You are a social media writer for Economic Times. Be concise and compliant.
Never use: guaranteed returns, risk-free, assured returns.
Always add: "Consult a SEBI-registered advisor before investing." for financial products.
"telegram": "conversational tone, 150 words max, mix of emojis and hashtags"

Topic summary: {key_context}

Write THREE social media posts. Respond with ONLY this JSON (no markdown, no extra keys):
{{
  "linkedin": "write the linkedin post text here directly as a string",
  "twitter": "write the twitter post text here directly as a string, max 240 chars",
  "instagram": "write the instagram post text here directly as a string",
  "telegram": "conversational tone, 150 words max, mix of emojis and hashtags, suitable for a Telegram channel"

}}

CRITICAL: Each value must be a plain string. NOT a nested object. NOT {{"linkedin": "..."}}.

Topic summary: {key_context}

Write THREE social media posts. Respond with ONLY this JSON (no markdown):
{{
  "linkedin": "Professional tone, 100 words max, 2 hashtags, ends with CTA",
  "twitter": "Max 240 chars, 1 hashtag",
  "instagram": "casual tone, 80 words, 3 hashtags"
}}
"""

FAQ_PROMPT = """
You are writing an internal FAQ for Economic Times editorial team.

Product context: {research_brief}

Write 5 FAQ entries. Respond with ONLY this JSON (no markdown):
{{
  "faqs": [
    {{"question": "...", "answer": "..."}}
  ]
}}
"""

REWRITE_PROMPT = """
Rewrite ONLY this sentence to fix the compliance issue. Return only the rewritten sentence.

Original: {flagged_sentence}
Issue: {issue_description}
Fix direction: {rewrite_suggestion}

REWRITE RULES (MANDATORY):
- If a sentence was flagged for an unverified statistic, REMOVE the number entirely
- Do NOT replace a flagged number with a different number
- Rewrite qualitatively: "delivered significant gains" not "delivered 105% gains"

"""


def _parse_brief(research_brief: str) -> dict:
    try:
        return json.loads(research_brief)
    except (json.JSONDecodeError, TypeError):
        return {}


def _build_feedback_section(state: ContentState) -> str:
    if not state.get("violations"):
        return ""
    lines = ["PREVIOUS REVIEW FEEDBACK — fix these issues before resubmitting:"]
    for v in state["violations"]:
        lines.append(f'  - Sentence: "{v.get("sentence","")}"')
        lines.append(f'    Issue: {v.get("description", v.get("rule",""))}')
        lines.append(f'    Suggested fix: {v.get("rewrite_suggestion","")}')
    return "\n".join(lines)


def drafter_node(state: ContentState) -> ContentState:
    print("DEBUG DRAFTER - violations:", len(state.get("violations", [])), "blog_post:", len(state.get("blog_post", "")))  # ADD THIS
    large_llm = get_large_llm(temperature=0.7)
    small_llm = get_small_llm(temperature=0.5)

    brief = _parse_brief(state["research_brief"])
    key_context = brief.get("KEY_CONTEXT", state["raw_input"][:300])
    feedback_section = _build_feedback_section(state)

    # ── If this is a rewrite cycle, do targeted sentence rewrites only ────────
    if state.get("violations") and state.get("blog_post"):
        blog = state["blog_post"]
        for v in state["violations"]:
            flagged = v.get("sentence", "")
            if not flagged:
                continue
            flagged = strip_unverified_stats(flagged, state.get("confidence_scores", {}))
            rewrite_prompt = REWRITE_PROMPT.format(
                flagged_sentence=flagged,
                issue_description=v.get("description", v.get("rule", "")),
                rewrite_suggestion=v.get("rewrite_suggestion", ""),
            )
            rewritten = call_llm_json(large_llm, rewrite_prompt, label="drafter-rewrite").strip()
            if rewritten and flagged in blog:
                blog = blog.replace(flagged, rewritten)

        # Generate telegram if not already in state
        if not state.get("social_posts", {}).get("telegram"):
            telegram_prompt = f"""Write a Telegram channel post for Economic Times about this topic:
{key_context[:300]}

Requirements:
- Conversational tone
- 100-150 words
- Use emojis
- End with hashtags
- Include: "Consult a SEBI-registered advisor before investing."

Return ONLY the post text, no JSON, no markdown.
"""
            telegram_content = call_llm_json(large_llm, telegram_prompt, label="drafter-telegram").strip()
            current_social = state.get("social_posts", {})
            current_social["telegram"] = telegram_content
            state = {**state, "social_posts": current_social}

        entry = log_decision(
            state, "drafter", "TARGETED REWRITE",
            f"Rewrote {len(state['violations'])} flagged sentence(s) — retry #{state['retry_count']}"
        )
        return {**state, "blog_post": blog, "violations": [], "audit_log": [entry]}
    # ── Fresh draft ───────────────────────────────────────────────────────────
    # 1. Blog post (large model)
    blog_prompt = BLOG_PROMPT.format(
        constitution=ET_STYLE_CONSTITUTION,
        research_brief=state["research_brief"][:1500],
        feedback_section=feedback_section,
    )
    blog_post = call_llm_json(large_llm, blog_prompt, label="drafter-blog").strip()

    # 2. Social posts (small model)
    social_prompt = SOCIAL_PROMPT.format(
        key_context=key_context[:400],
    )
    social_raw = call_llm_json(small_llm, social_prompt, label="drafter-social").strip()
    social_clean = social_raw.strip("```json").strip("```").strip()

    if not social_clean.endswith("}"):
        social_clean = social_clean + '"}'

    def extract_text(val):
        while isinstance(val, dict):
            val = next(iter(val.values()))
        return str(val).strip()

    try:
        parsed = json.loads(social_clean)
        social_posts = {
            "linkedin":  extract_text(parsed.get("linkedin", "")),
            "twitter":   extract_text(parsed.get("twitter", "")),
            "instagram": extract_text(parsed.get("instagram", "")),
        }
    except json.JSONDecodeError:
        social_posts = {}
        for platform in ("linkedin", "twitter", "instagram"):
            match = re.search(rf'"{platform}"\s*:\s*"(.*?)(?:"\s*[,}}]|$)', social_clean, re.DOTALL)
            social_posts[platform] = match.group(1).strip() if match else ""

    # Generate Telegram post separately
    telegram_prompt = f"""Write a Telegram channel post for Economic Times about this topic:
{key_context[:300]}

Requirements:
- Conversational tone
- 100-150 words
- Use emojis
- End with hashtags
- Include: "Consult a SEBI-registered advisor before investing."

Return ONLY the post text, no JSON, no markdown.
"""
    telegram_content = call_llm_json(small_llm, telegram_prompt, label="drafter-telegram").strip()
    social_posts["telegram"] = telegram_content

    # 3. FAQ (small model)
    faq_prompt = FAQ_PROMPT.format(
        research_brief=state["research_brief"][:600],
    )
    faq_raw = call_llm_json(small_llm, faq_prompt, label="drafter-faq").strip()
    faq_clean = faq_raw.strip("```json").strip("```").strip()
    try:
        faq_data = json.loads(faq_clean)
        faq = json.dumps(faq_data)
    except json.JSONDecodeError:
        faq = faq_raw

    entry = log_decision(
        state, "drafter", "DRAFT COMPLETE",
        "Blog (700w) + 3 social variants + FAQ generated. Passing to Reviewer."
    )
    return {
        **state,
        "blog_post": blog_post,
        "social_posts": social_posts,
        "faq": faq,
        "violations": [],
        "audit_log": [entry],
    }