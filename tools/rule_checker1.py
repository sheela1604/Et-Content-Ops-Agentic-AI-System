import re
from dataclasses import dataclass
from typing import List


@dataclass
class Violation:
    sentence: str
    rule_id: str
    severity: str          # BLOCK | FLAG
    description: str
    rewrite_suggestion: str


# ── Rule catalogue ────────────────────────────────────────────────────────────
RULES = [
    {
        "id": "SEBI-001",
        "severity": "BLOCK",
        "pattern": r"guaranteed.{0,25}return|assured.{0,25}return|guaranteed.{0,25}profit",
        "description": "Guaranteed returns prohibited — SEBI circular 2023",
        "rewrite_suggestion": "Replace with: 'has historically generated returns of up to X%'",
    },
    {
        "id": "SEBI-002",
        "severity": "BLOCK",
        "pattern": r"\brisk[\s\-]{0,5}free\b|zero[\s\-]{0,5}risk|no[\s\-]{0,5}risk\b",
        "description": "Risk-free claims prohibited for all investment products",
        "rewrite_suggestion": "Replace with: 'carries a relatively lower risk profile'",
    },
    {
        "id": "SEBI-003",
        "severity": "BLOCK",
        "pattern": r"will\s+give.{0,20}\d+\s*%.{0,10}return|will\s+return.{0,10}\d+\s*%",
        "description": "Forward-looking guaranteed return percentages prohibited",
        "rewrite_suggestion": "Replace with: 'has historically delivered X% returns as of [date]'",
    },
    {
        "id": "SEBI-004",
        "severity": "BLOCK",
        "pattern": r"double.{0,20}money|triple.{0,20}money|10x.{0,20}returns",
        "description": "Misleading return multiplier claims prohibited",
        "rewrite_suggestion": "Remove claim or cite verified historical data with source",
    },
    {
        "id": "IRDAI-001",
        "severity": "FLAG",
        "pattern": r"\d+\s*%.{0,20}(return|yield|growth).{0,20}(insurance|policy|plan|ulip)",
        "description": "Insurance return claims require IRDAI disclaimer",
        "rewrite_suggestion": "Add: 'Subject to policy terms and conditions. Past performance not indicative of future results.'",
    },
    {
        "id": "ET-BRAND-001",
        "severity": "FLAG",
        "pattern": r"\bbest in class\b|\bnumber[\s\-]?one\b|\b#\s*1\b|\btop[\s\-]rated\b|\bbest[\s\-]in[\s\-]india\b",
        "description": "Superlatives require a cited source — ET brand guidelines",
        "rewrite_suggestion": "Add source: 'ranked #1 by [Publication, Year]' or rephrase without superlative",
    },
    {
        "id": "ET-BRAND-002",
        "severity": "FLAG",
        "pattern": r"\b100\s*%\s*(accurate|safe|secure|reliable)\b",
        "description": "Absolute accuracy/safety claims prohibited without evidence",
        "rewrite_suggestion": "Qualify: 'designed with enterprise-grade security' or cite specific certifications",
    },
    {
        "id": "DISCLAIMER-001",
        "severity": "FLAG",
        "pattern": r"invest|mutual fund|stock|equity|portfolio|sip",
        "description": "Investment content requires SEBI disclaimer",
        "rewrite_suggestion": "Ensure footer includes: 'Consult a SEBI-registered investment advisor before investing.'",
    },
]


def check_rules(content: str) -> List[Violation]:
    """
    Deterministic rule check. Splits content into sentences,
    tests each against every rule pattern. Returns all violations found.
    """
    violations: List[Violation] = []
    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())

    for sentence in sentences:
        if not sentence.strip():
            continue
        for rule in RULES:
            if re.search(rule["pattern"], sentence, re.IGNORECASE):
                violations.append(
                    Violation(
                        sentence=sentence,
                        rule_id=rule["id"],
                        severity=rule["severity"],
                        description=rule["description"],
                        rewrite_suggestion=rule["rewrite_suggestion"],
                    )
                )
    return violations


def has_hard_blocks(violations: List[Violation]) -> bool:
    return any(v.severity == "BLOCK" for v in violations)


def violations_to_dict(violations: List[Violation]) -> List[dict]:
    return [
        {
            "sentence": v.sentence,
            "rule": v.rule_id,
            "severity": v.severity,
            "description": v.description,
            "rewrite_suggestion": v.rewrite_suggestion,
        }
        for v in violations
    ]
