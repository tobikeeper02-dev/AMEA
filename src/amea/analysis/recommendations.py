"""Generate strategic recommendations based on scoring outputs."""
from __future__ import annotations

from typing import Dict


ENTRY_MODES = {
    "market expansion": {
        "high": "Greenfield investment with localized fulfillment network",
        "medium": "Joint venture with established regional partner",
        "low": "Lightweight partnership or distributor-led entry",
    },
    "partnership scouting": {
        "high": "Strategic alliance with leading incumbents to unlock distribution scale",
        "medium": "Pilot partnership with regional specialists before wider rollout",
        "low": "Supplier benchmarking program to qualify potential collaborators",
    },
    "investment diligence": {
        "high": "Pursue majority investment with integration roadmap and value-creation plan",
        "medium": "Structure minority stake with governance rights and staged capital deployment",
        "low": "Monitor through scouting network while addressing red-flag diligence gaps",
    },
}


TURNAROUND_PLAYBOOK = {
    "risk": "Institute robust risk governance and scenario planning to mitigate political shocks.",
    "cost_efficiency": "Prioritize automation and shared-services sourcing to offset higher labor costs.",
    "growth": "Sequence rollout through digitally native customer segments before wider expansion.",
    "sustainability": "Embed sustainability metrics in supplier scorecards and explore renewable PPAs.",
    "digital": "Accelerate digital maturity via strategic alliances with local technology providers.",
}


def select_entry_mode(composite_score: float, use_case: str) -> str:
    key = use_case.lower()
    library = ENTRY_MODES.get(key, ENTRY_MODES["market expansion"])
    if composite_score >= 70:
        return library["high"]
    if composite_score >= 50:
        return library["medium"]
    return library["low"]


def build_turnaround_actions(dimension_scores: Dict[str, float]) -> Dict[str, str]:
    """Return targeted improvement actions for weaker dimensions."""
    actions: Dict[str, str] = {}
    for key, score in dimension_scores.items():
        if score < 55:
            actions[key] = TURNAROUND_PLAYBOOK[key]
    return actions
