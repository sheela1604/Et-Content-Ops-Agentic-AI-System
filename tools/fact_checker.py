import re
import json
from typing import Dict


def check_facts(content: str, research_brief_str: str) -> Dict[str, str]:
    """
    Extracts numeric/statistical claims from content and checks whether
    each appears in the research brief's VERIFIED_FACTS.

    Returns dict: { claim_text: "verified" | "unverified" | "blocked" }
    """
    if not research_brief_str:
        return {}

    try:
        brief = json.loads(research_brief_str)
    except (json.JSONDecodeError, TypeError):
        return {}

    verified_texts = " ".join(
        f.get("claim", "") for f in brief.get("VERIFIED_FACTS", [])
    ).lower()
    unverified_texts = " ".join(
        f.get("claim", "") for f in brief.get("UNVERIFIED_CLAIMS", [])
    ).lower()

    # Pattern: numbers with financial/metric suffixes
    stat_pattern = r"[\d,]+\.?\d*\s*(?:%|crore|lakh|billion|million|thousand|x\b)"
    found_stats = re.findall(stat_pattern, content, re.IGNORECASE)

    scores: Dict[str, str] = {}
    for stat in set(found_stats):
        stat_lower = stat.lower().strip()
        if stat_lower in verified_texts:
            scores[stat] = "verified"
        elif stat_lower in unverified_texts:
            scores[stat] = "blocked"
        else:
            scores[stat] = "unverified"

    return scores


def get_hallucination_risks(scores: Dict[str, str]) -> list:
    """Return claims that appear in content but were never in the research brief."""
    return [claim for claim, status in scores.items() if status == "unverified"]
