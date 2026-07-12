from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas_core.config_loader import PROJECT_ROOT
from atlas_core.models import Recommendation
from atlas_core.utils.time_utils import utc_now


class JournalEngine:
    """Recommendation back-book and journal engine for the technical MVP."""

    def __init__(self, journal_dir: str | Path = "data/journal"):
        base = Path(journal_dir)
        if not base.is_absolute():
            base = PROJECT_ROOT / base
        base.mkdir(parents=True, exist_ok=True)
        self.journal_dir = base
        self.recommendations_path = base / "recommendations.jsonl"

    def back_book_record(self, recommendation: Recommendation) -> dict[str, Any]:
        tp = recommendation.trade_plan
        cc = recommendation.chart_context
        cat = recommendation.catalyst_context
        fc = recommendation.fundamental_context
        return {
            "status": "tracked",
            "created_at": recommendation.created_at.isoformat(),
            "symbol": recommendation.asset.symbol,
            "name": recommendation.asset.name,
            "intent": recommendation.intent,
            "strategy": recommendation.strategy,
            "verdict": recommendation.verdict,
            "atlas_score": recommendation.atlas_score,
            "portfolio_fit": recommendation.portfolio_fit.score,
            "entry": [tp.entry_low, tp.entry_high] if tp else None,
            "stop_loss": tp.stop_loss if tp else None,
            "take_profit": [tp.take_profit_1, tp.take_profit_2, tp.take_profit_3] if tp else None,
            "do_not_chase_above": tp.do_not_chase_above if tp else None,
            "reward_risk_ratio": tp.reward_risk_ratio if tp else None,
            "chart": {
                "trend_status": cc.trend_status,
                "setup_type": cc.setup_type,
                "rsi_14": cc.rsi_14,
                "atr_pct": cc.atr_pct,
                "support_1": cc.support_1,
                "resistance_1": cc.resistance_1,
            } if cc else {},
            "catalyst": {
                "score": cat.score,
                "news_count": cat.news_count,
                "primary_catalyst": cat.primary_catalyst,
                "risk_flags": cat.risk_flag_count,
            } if cat else {},
            "fundamentals": {
                "overall_score": fc.overall_score,
                "classification": fc.classification,
                "quality_score": fc.quality_score,
                "growth_score": fc.growth_score,
                "valuation_score": fc.valuation_score,
            } if fc else {},
            "review_checkpoints": {
                "after_7_days": "pending",
                "after_14_days": "pending",
                "after_30_days": "pending",
                "after_60_days": "pending",
            },
        }

    def append_recommendations(self, recommendations: list[Recommendation]) -> Path:
        with self.recommendations_path.open("a", encoding="utf-8") as handle:
            for rec in recommendations:
                handle.write(json.dumps(self.back_book_record(rec), sort_keys=True, default=str) + "\n")
        return self.recommendations_path

    def save_recommendation(self, recommendation: Recommendation) -> str:
        """Backward-compatible Sprint 0-6 helper used by tests and scripts."""
        symbol = recommendation.asset.symbol.upper()
        ts = recommendation.created_at.strftime("%Y%m%dT%H%M%S")
        path = self.journal_dir / f"{ts}_{symbol}_recommendation.json"
        path.write_text(json.dumps(self.back_book_record(recommendation), indent=2, sort_keys=True, default=str), encoding="utf-8")
        return str(path)

    def read_recommendations(self, limit: int = 200) -> list[dict[str, Any]]:
        if not self.recommendations_path.exists():
            return []
        lines = self.recommendations_path.read_text(encoding="utf-8").splitlines()[-limit:]
        out: list[dict[str, Any]] = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def summarize_recommendations(self) -> dict[str, Any]:
        rows = self.read_recommendations(limit=1000)
        if not rows:
            return {"count": 0, "message": "No recommendation history yet."}
        avg_score = sum(float(r.get("atlas_score", 0)) for r in rows) / len(rows)
        by_strategy: dict[str, int] = {}
        for row in rows:
            strategy = str(row.get("strategy", "unknown"))
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
        return {
            "count": len(rows),
            "avg_atlas_score": round(avg_score, 2),
            "by_strategy": by_strategy,
            "last_updated": utc_now().isoformat(),
        }
