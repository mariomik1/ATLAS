from __future__ import annotations

from atlas_core.models import FactorScore, ScoreBreakdown


class AtlasScoreEngine:
    def combine(self, factors: list[FactorScore]) -> ScoreBreakdown:
        total_weight = sum(f.weight for f in factors)
        if total_weight <= 0:
            raise ValueError("Total score weight must be positive")
        weighted = sum(f.score * f.weight for f in factors) / total_weight
        data_penalty = 0
        for factor in factors:
            if factor.data_quality.level in {"partial", "missing"}:
                data_penalty += 4
            if factor.data_quality.level == "sample":
                data_penalty += 1
        total = max(0, min(100, weighted - data_penalty))
        confidence = max(0, min(100, total - data_penalty * 2))
        return ScoreBreakdown(total_score=round(total, 2), factors=factors, confidence_pct=round(confidence, 2))
