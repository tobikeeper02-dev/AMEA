"""Generate strategic recommendations based on scoring outputs."""
from __future__ import annotations

from typing import Dict


ENTRY_MODES = {
    "high": "Greenfield investment with localized fulfillment network",
    "medium": "Joint venture with established regional partner",
    "low": "Lightweight partnership or distributor-led entry",
}


TURNAROUND_PLAYBOOK = {
    "risk": "Institute robust risk governance and scenario planning to mitigate political shocks.",
    "cost_efficiency": "Prioritize automation and shared-services sourcing to offset higher labor costs.",
    "growth": "Sequence rollout through digitally native customer segments before wider expansion.",
    "sustainability": "Embed sustainability metrics in supplier scorecards and explore renewable PPAs.",
    "digital": "Accelerate digital maturity via strategic alliances with local technology providers.",
}


def select_entry_mode(composite_score: float) -> str:
    if composite_score >= 70:
        return ENTRY_MODES["high"]
    if composite_score >= 50:
        return ENTRY_MODES["medium"]
    return ENTRY_MODES["low"]


def build_turnaround_actions(dimension_scores: Dict[str, float]) -> Dict[str, str]:
    """Return targeted improvement actions for weaker dimensions."""
    actions: Dict[str, str] = {}
    for key, score in dimension_scores.items():
        if score < 55:
            actions[key] = TURNAROUND_PLAYBOOK[key]
    return actions
