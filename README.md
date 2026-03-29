# ET Content Ops — AI Agent System
### ET GenAI Hackathon 2026 · Track 1: AI for Enterprise Content Operations

> **From raw product spec to published, compliant, localized, multi-channel content in under 90 seconds.**
> Manual equivalent: ~4 hours. That's a 195x speedup.

---

## What We Built

ET Content Ops is a fully autonomous, multi-agent AI pipeline that handles the complete enterprise content lifecycle — creation, compliance review, localization, and multi-channel distribution — with minimal human intervention.

This is not a chatbot. This is not a single-prompt wrapper. It is a stateful, self-correcting agent graph that:

- Classifies any input and routes it to the correct pipeline automatically
- Drafts publish-ready blog posts, social content, and FAQs from raw specs
- Enforces SEBI, IRDAI, and brand compliance through a 5-layer guardrail system
- Autonomously rewrites flagged content and retries — up to 3 times — before escalating to a human
- Localizes content to Hindi and Tamil with cultural adaptation
- Distributes to ET Digital, LinkedIn, Twitter, Instagram, and live Telegram channel
- Logs every agent decision in a full audit trail

---

## Evaluation Rubric — How We Score

### Autonomy Depth (30%)

The system completes 8 steps without human involvement:

1. Input classification and routing (Supervisor)
2. Fact extraction and research brief generation (Researcher)
3. Blog post + social + FAQ drafting (Drafter)
4. Deterministic compliance rule checking (Reviewer Layer 3)
5. Fact hallucination detection (Reviewer Layer 4a)
6. LLM semantic compliance review (Reviewer Layer 4b)
7. Autonomous targeted rewrite of flagged sentences (Drafter retry)
8. Localization to Hindi and Tamil (Localizer)

**Failure recovery:** When the Reviewer fails content, the Drafter automatically rewrites only the flagged sentences and resubmits. This retry loop runs up to 3 times autonomously. After 3 failures, it escalates to the Human Gate with the full audit trail — rather than crashing or looping forever.

**Branching logic:** 3 distinct pipeline paths based on input type (PRODUCT_SPEC, COMPLIANCE_CHECK, ENGAGEMENT_DATA), controlled by conditional edge functions in LangGraph.

---

### Multi-Agent Design (20%)

5 agents with clear, non-overlapping responsibilities:

| Agent | Model | Responsibility |
|-------|-------|---------------|
| Supervisor | llama-3.1-8b | Classifies input type, routes to correct pipeline |
| Researcher | llama-3.1-8b | Extracts verified facts from spec + live ET RSS feeds |
| Drafter | llama-3.1-8b | Generates blog, social posts, FAQ; rewrites flagged sentences |
| Reviewer | llama-3.1-8b | 5-layer compliance check — deterministic + LLM |
| Localizer / Strategy | llama-3.1-8b | Hindi/Tamil localization OR engagement strategy + calendar |

**Communication:** All agents share a single `ContentState` TypedDict. No direct agent-to-agent calls. LangGraph enforces the handoff contract and maintains state across the entire pipeline.

**Orchestration:** Conditional edge functions in `graph.py` control routing — the graph is not a linear chain but a stateful machine with loops, branches, and escalation paths.

---

### Technical Creativity (20%)

**Cost-efficiency routing (bonus criteria):**
- Small model (llama-3.1-8b via Groq) handles all classification, rule-matching, and translation
- Same model handles drafting via Groq's free API — keeping cost to zero
- Deterministic regex handles SEBI rule checking with no LLM call at all (Layer 3)
- LLM is only called for tasks that genuinely require reasoning

**5-layer compliance system (cheapest first):**

| Layer | Type | Cost |
|-------|------|------|
| 1 | Pre-generation fact separation | Free — prompt engineering |
| 2 | ET Style Constitution injection | Free — prompt engineering |
| 3 | SEBI/IRDAI/brand regex rules | Free — no LLM |
| 4a | Stat hallucination detection | Free — string matching |
| 4b | LLM semantic review | 1 LLM call |
| 5 | Human gate with full audit trail | Human decision |

**Anti-hallucination stat stripping:** When a sentence is flagged for an unverified statistic, code deterministically strips the number before sending to the LLM for rewrite — preventing the model from substituting another hallucinated figure.

**Live distribution:** Content is published to a live Telegram channel via Telegram Bot API on every pipeline run. The webhook integration via Make also enables routing to any external platform.

---

### Enterprise Readiness (20%)

**Error handling:**
- RSS fetch failures silently skip and continue — pipeline never blocks on external data
- Groq rate limits trigger graceful retry with backoff
- JSON parse failures fall back to regex extraction for social posts
- All exceptions are caught per-agent — one agent failure does not crash the pipeline

**Compliance guardrails:**
- SEBI-001 through SEBI-004: guaranteed/assured returns, risk-free claims, forward-looking guarantees, unrealistic return multiples — all BLOCK
- IRDAI-001: insurance return percentage claims — FLAG
- ET-BRAND-001/002: unsourced superlatives, absolute accuracy claims — FLAG
- Fact cross-reference: every percentage in the content is checked against the research brief

**Audit trail:**
Every agent decision is logged with timestamp, agent name, decision, reasoning, and retry count. The full trail is visible in the dashboard and saved to the output JSON.

**Human-in-the-loop:**
The Human Gate presents the full blog excerpt, compliance violation table with exact sentences and suggested rewrites, fact confidence scores, and audit trail to the human editor before any publish action. In demo mode this auto-approves; in production mode it is interactive.

**Graceful degradation:**
If the reviewer cannot parse the LLM's compliance response, it defaults to PASS rather than crashing — with the parse error logged in the audit trail.

---

### Impact Quantification (10%)

| Metric | Agent | Manual |
|--------|-------|--------|
| Product Launch Sprint | ~75 seconds | ~4 hours |
| Compliance Rejection | ~10 seconds | ~30 minutes |
| Performance Pivot | ~6 seconds | ~2 hours |
| **Speedup** | — | **~195x** |

Run `python tests/benchmark.py` to reproduce these numbers live.

**Content consistency:** Every run produces content that passes the same SEBI ruleset deterministically. Human editors never see a draft with a guaranteed-returns claim — it is caught and rewritten before it reaches the gate.

---

## Judge Scenarios

| # | Scenario | Input | Output |
|---|----------|-------|--------|
| 1 | Product Launch Sprint | NovaPay SmartSave product spec | Blog post + LinkedIn + Twitter + Instagram + Telegram posts + FAQ + Hindi + Tamil localization |
| 2 | Compliance Rejection | Blog draft with SEBI violations | Violations flagged with exact sentence + rule ID + compliant rewrite |
| 3 | Performance Pivot | Q1 engagement data (video 4.7x > text) | Strategy recommendation + 4-week video-weighted content calendar |

All 3 scenarios complete end-to-end with no crashes. Run them with:

```bash
python main.py
# then type: a
```

---

## Architecture

```
INPUT
  │
  ▼
Supervisor ──────────────────────────────────────────────────────────┐
  │                                                                   │
  ├─ PRODUCT_SPEC ──► Researcher ──► Drafter ──► Reviewer ──► Human Gate ──► Localizer ──► Publisher
  │                                      ▲            │
  │                                      └── RETRY ───┘ (max 3x)
  │
  ├─ COMPLIANCE_CHECK ──────────────────► Reviewer ──► Human Gate
  │
  └─ ENGAGEMENT_DATA ───────────────────────────────► Strategy ──► END
```

**Tech stack:**

| Component | Technology |
|-----------|-----------|
| Agent framework | LangGraph 0.2+ |
| LLM provider | Groq API (llama-3.1-8b-instant) |
| Fallback providers | Anthropic Claude, Google Gemini, Ollama (local) |
| Language | Python 3.14 |
| Web framework | FastAPI + uvicorn |
| Frontend | Static HTML dashboard |
| Distribution | Telegram Bot API + Make webhook |
| Compliance | Deterministic regex + LLM semantic review |

---

## Setup

### Prerequisites
- Python 3.11+ (3.14 supported)
- Groq API key — free at [console.groq.com](https://console.groq.com) (no credit card needed)

### Install

```bash
cd et_content_ops
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
pip install langchain-groq
```

### Configure `.env`

```
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
DEMO_AUTO_APPROVE=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_channel_id
MAKE_WEBHOOK_URL=your_webhook_url
```

### Run

```bash
# CLI — run all 3 judge scenarios
python main.py
# type: a

# UI Dashboard
uvicorn ui.api:api --reload --port 8000
# open ui/dashboard.html in browser

# Benchmark
cd tests
python benchmark.py
```

---

## Project Structure

```
et_content_ops/
├── main.py                  ← CLI entry point
├── graph.py                 ← LangGraph wiring — nodes + conditional edges
├── state.py                 ← Shared ContentState TypedDict
├── requirements.txt
├── .env
│
├── agents/
│   ├── supervisor.py        ← Input classifier + routing logic
│   ├── researcher.py        ← RSS + web scraping + research brief
│   ├── drafter.py           ← Blog / social / FAQ + targeted rewrite
│   ├── reviewer.py          ← 5-layer compliance checker
│   ├── human_gate.py        ← Approval checkpoint with audit display
│   ├── localizer.py         ← Hindi/Tamil + strategy/calendar
│   └── publisher.py         ← Multi-channel distribution
│
├── tools/
│   ├── rule_checker.py      ← Deterministic SEBI/IRDAI/brand regex rules
│   ├── fact_checker.py      ← Cross-reference stats vs research brief
│   ├── web_tools.py         ← RSS fetcher (4 ET feeds) + web scraper
│   └── audit.py             ← Structured audit logger
│
├── config/
│   └── llm.py               ← LLM client factory — Groq/Anthropic/Gemini/Ollama
│
├── scenarios/
│   └── inputs.py            ← All 3 judge scenario inputs
│
├── ui/
│   ├── api.py               ← FastAPI backend
│   └── dashboard.html       ← Live agent trace dashboard
│
├── tests/
│   └── benchmark.py         ← Impact quantification
│
└── outputs/                 ← Generated JSON outputs (auto-created)
```

---

## What Makes This Different

Most hackathon submissions generate content with a single LLM call. ET Content Ops is different in three ways:

**1. True autonomy with failure recovery** — the system does not just generate and stop. It reviews its own output, identifies non-compliant sentences, rewrites them, and resubmits — multiple times — before asking a human for help. The human gate is a safety net, not a crutch.

**2. Compliance that cannot be bypassed** — SEBI violations are caught by deterministic code before the LLM even sees the content for rewrite. A hallucinated statistic is stripped by code, not by asking the LLM to remove it. This means compliance is enforced even when the LLM misbehaves.

**3. Cost efficiency without sacrificing quality** — the entire pipeline runs on Groq's free tier using an 8B parameter model. We route tasks by complexity: regex for rule-checking, small LLM for classification and localization, same model for drafting. No GPT-4, no paid API, zero cost per run.

---

*ET GenAI Hackathon 2026 · Track 1: AI for Enterprise Content Operations*
