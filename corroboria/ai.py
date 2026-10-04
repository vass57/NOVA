"""Safe boundary for optional AI review suggestions.

No provider is configured in this prototype.  The validator is kept separate
so a challenge-approved provider can be added without letting model output
change a deterministic verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AiSuggestion:
    proposed_verdict: str
    evidence_references: tuple[str, ...]
    rule_ids: tuple[str, ...]
    missing_information: tuple[str, ...]
    next_step: str


def validate_suggestion(payload: dict[str, Any], allowed_rule_ids: set[str]) -> AiSuggestion:
    """Validate untrusted model output before it can be displayed as advice.

    A suggestion never becomes a final result: unresolved cases remain
    ``Needs review`` until a human records a decision.
    """

    required = {
        "proposed_verdict",
        "evidence_references",
        "rule_ids",
        "missing_information",
        "next_step",
    }
    missing = required.difference(payload)
    if missing:
        raise ValueError(f"AI response is missing: {', '.join(sorted(missing))}.")

    verdict = payload["proposed_verdict"]
    if verdict not in {"Actual anomaly", "Needs review"}:
        raise ValueError("AI may only propose 'Actual anomaly' or 'Needs review'.")
    if not isinstance(payload["rule_ids"], list) or not all(
        isinstance(rule, str) and rule in allowed_rule_ids for rule in payload["rule_ids"]
    ):
        raise ValueError("AI response contains an unknown rule identifier.")
    for key in ("evidence_references", "missing_information"):
        if not isinstance(payload[key], list) or not all(isinstance(item, str) for item in payload[key]):
            raise ValueError(f"AI response field '{key}' must be a list of strings.")
    if not isinstance(payload["next_step"], str) or not payload["next_step"].strip():
        raise ValueError("AI response must include a non-empty next_step.")

    return AiSuggestion(
        proposed_verdict=verdict,
        evidence_references=tuple(payload["evidence_references"]),
        rule_ids=tuple(payload["rule_ids"]),
        missing_information=tuple(payload["missing_information"]),
        next_step=payload["next_step"].strip(),
    )
