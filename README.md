# ET Content Ops Agent System
**ET GenAI Hackathon 2026 — Track 1: AI for Enterprise Content Operations**

---

## Architecture

```
Supervisor (llama3.2)
    ├── PRODUCT_SPEC   → Researcher → Drafter → Reviewer ⟲ → Human Gate → Localizer
    ├── COMPLIANCE_CHECK              → Reviewer → Human Gate
    └── ENGAGEMENT_DATA                                    → Strategy
```

5 agents · LangGraph state machine · 5-layer compliance guardrails · Full audit trail

---

## Prerequisites

### 1. Install Ollama
```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull llama3.2        # Supervisor, Reviewer, Localizer (small, fast)
ollama pull llama3.1:8b     # Researcher, Drafter (large, capable)
```

### 2. Install Python dependencies
```bash
cd et_content_ops
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env .env.local
# Edit .env.local if your Ollama runs on a different port
```

---

## Running the project

### Option A — CLI (recommended for development)
```bash
python main.py
# Select scenario 1/2/3 or 'a' to run all three
```

### Option B — UI Dashboard
```bash
# Terminal 1: start the API
export DEMO_AUTO_APPROVE=true
uvicorn ui.api:api --reload --port 8000

# Terminal 2: open the dashboard
open ui/dashboard.html        # macOS
xdg-open ui/dashboard.html    # Linux
# Or just open ui/dashboard.html in your browser
```

### Option C — Benchmark (impact quantification)
```bash
python tests/benchmark.py
# Prints agent time vs manual estimate table
# Saves results to outputs/benchmark.json
```

---

## Judge Scenarios

| # | Scenario | Input type | Expected output |
|---|----------|-----------|-----------------|
| 1 | Product Launch Sprint | PRODUCT_SPEC | Blog + 3 social variants + FAQ + Hindi localization |
| 2 | Compliance Rejection | COMPLIANCE_CHECK | Violations flagged + compliant rewrites suggested |
| 3 | Performance Pivot | ENGAGEMENT_DATA | Strategy recommendation + 4-week content calendar |

---

## Project structure

```
et_content_ops/
├── main.py                  ← CLI entry point
├── graph.py                 ← LangGraph wiring (all nodes + conditional edges)
├── state.py                 ← Shared ContentState TypedDict
├── requirements.txt
├── .env
│
├── agents/
│   ├── supervisor.py        ← Input classifier + routing logic
│   ├── researcher.py        ← RSS + web scraping + research brief
│   ├── drafter.py           ← Blog / social / FAQ / targeted rewrite
│   ├── reviewer.py          ← 4-layer compliance checker
│   ├── human_gate.py        ← Approval checkpoint
│   └── localizer.py         ← Hindi/Tamil + strategy/calendar
│
├── tools/
│   ├── rule_checker.py      ← Deterministic SEBI/IRDAI/brand rules
│   ├── fact_checker.py      ← Cross-reference stats vs research brief
│   ├── web_tools.py         ← RSS fetcher + web scraper
│   └── audit.py             ← Structured audit logger
│
├── config/
│   └── llm.py               ← Ollama client (large + small models)
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
└── outputs/                 ← Generated JSON outputs (git-ignored)
```

---

## Compliance guardrails (5 layers)

| Layer | Type | What it catches |
|-------|------|----------------|
| 1 | Pre-generation | Researcher separates VERIFIED vs UNVERIFIED facts |
| 2 | In-generation | ET Style Constitution injected into every Drafter prompt |
| 3 | Post-generation (deterministic) | SEBI/IRDAI/brand regex rules — no LLM |
| 4a | Post-generation (fact check) | Stats in content cross-referenced vs research brief |
| 4b | Post-generation (semantic LLM) | Nuanced implication, missing disclaimers |
| 5 | Human gate | Editor reviews full audit trail before publish |

---

## Cost-efficiency routing

- `llama3.2` (small): Supervisor classification, Reviewer rule matching, Localizer translation
- `llama3.1:8b` (large): Researcher synthesis, Drafter blog/social/FAQ creation

This qualifies for the **Technical Creativity cost-efficiency bonus** in the rubric.
