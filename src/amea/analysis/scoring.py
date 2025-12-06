"""Scoring helpers for country comparison."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping


@dataclass
class ScoreBreakdown:
    dimension_scores: Dict[str, float]
    composite: float

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> "ScoreBreakdown":
        if payload is None:
            return cls(dimension_scores={}, composite=0.0)

        composite_raw = payload.get("composite") if isinstance(payload, Mapping) else None
        try:
            composite = float(composite_raw) if composite_raw is not None else 0.0
        except (TypeError, ValueError):
            composite = 0.0

        dimension_scores: Dict[str, float] = {}
        if isinstance(payload, Mapping):
            dimensions = payload.get("dimensions", {})
            if not isinstance(dimensions, Mapping):
                dimensions = {
                    key: value
                    for key, value in payload.items()
                    if key not in {"composite", "overall", "dimensions"}
                }
            for key, value in dimensions.items():
                try:
                    dimension_scores[key] = float(value)
                except (TypeError, ValueError):
                    continue

            if not dimension_scores and "overall" in payload:
                try:
                    composite = float(payload["overall"])
                except (TypeError, ValueError):
                    pass

        return cls(dimension_scores=dimension_scores, composite=composite)


__all__ = ["ScoreBreakdown"]
