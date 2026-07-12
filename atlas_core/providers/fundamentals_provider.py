from __future__ import annotations

import csv
import os
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, Optional

from atlas_core.config_loader import PROJECT_ROOT
from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import CompanyProfile, DataQuality, FundamentalContext, FundamentalMetrics
from atlas_core.utils.indicators import clamp
from atlas_core.utils.time_utils import utc_now
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.providers.http_client import JsonHttpClient


class FundamentalsProvider(ABC):
    name: str

    @abstractmethod
    def get_context(self, symbol: str) -> FundamentalContext:
        raise NotImplementedError

    def get_profile(self, symbol: str) -> Optional[CompanyProfile]:
        context = self.get_context(symbol)
        return context.profile

    def get_metrics(self, symbol: str) -> Optional[FundamentalMetrics]:
        context = self.get_context(symbol)
        return context.metrics


class CsvSampleFundamentalsProvider(FundamentalsProvider):
    """Offline-first fundamentals provider used in Sprint 4."""

    name = "csv_sample_fundamentals"

    def __init__(self, csv_path: str | Path = "data/samples/fundamentals.csv"):
        path = Path(csv_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        self.csv_path = path
        self._records = self._load_records()

    def get_context(self, symbol: str) -> FundamentalContext:
        normalized = symbol.strip().upper()
        context = self._records.get(normalized)
        if context:
            return context
        return FundamentalContext(
            symbol=normalized,
            overall_score=45,
            classification="missing",
            risks=["No fundamental record is available for this symbol in Sprint 4 sample data."],
            missing_fields=["all"],
            data_quality=DataQuality(
                level=DataQualityLevel.MISSING,
                provider=self.name,
                as_of=utc_now(),
                issues=["Missing sample fundamentals; use a live provider or extend fundamentals.csv."],
            ),
        )

    def _load_records(self) -> dict[str, FundamentalContext]:
        if not self.csv_path.exists():
            return {}
        records: dict[str, FundamentalContext] = {}
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                symbol = row.get("symbol", "").strip().upper()
                if not symbol:
                    continue
                quality = DataQuality(
                    level=DataQualityLevel(row.get("data_quality", "sample") or "sample"),
                    provider=self.name,
                    as_of=utc_now(),
                    issues=["Sprint 4 sample fundamentals. Replace with licensed/live provider before real decisions."],
                )
                profile = CompanyProfile(
                    symbol=symbol,
                    name=row.get("company_name") or row.get("name") or symbol,
                    asset_class=AssetClass(row.get("asset_class", "stock") or "stock"),
                    sector=self._clean(row.get("sector")),
                    industry=self._clean(row.get("industry")),
                    theme=self._clean(row.get("theme")),
                    country=self._clean(row.get("country")),
                    exchange=self._clean(row.get("exchange")),
                    currency=row.get("currency") or "USD",
                    isin=self._clean(row.get("isin")),
                    wkn=self._clean(row.get("wkn")),
                    website=self._clean(row.get("website")),
                    description=self._clean(row.get("description")),
                    data_quality=quality,
                )
                metrics = FundamentalMetrics(
                    symbol=symbol,
                    market_cap_usd=self._float(row.get("market_cap_usd")),
                    revenue_growth_yoy_pct=self._float(row.get("revenue_growth_yoy_pct")),
                    eps_growth_yoy_pct=self._float(row.get("eps_growth_yoy_pct")),
                    gross_margin_pct=self._float(row.get("gross_margin_pct")),
                    operating_margin_pct=self._float(row.get("operating_margin_pct")),
                    net_margin_pct=self._float(row.get("net_margin_pct")),
                    roe_pct=self._float(row.get("roe_pct")),
                    roic_pct=self._float(row.get("roic_pct")),
                    debt_to_equity=self._float(row.get("debt_to_equity")),
                    free_cash_flow_yield_pct=self._float(row.get("free_cash_flow_yield_pct")),
                    pe_ttm=self._float(row.get("pe_ttm")) or self._float(row.get("pe_ratio")),
                    forward_pe=self._float(row.get("forward_pe")),
                    peg_ratio=self._float(row.get("peg_ratio")),
                    dividend_yield_pct=self._float(row.get("dividend_yield_pct")),
                    beta=self._float(row.get("beta")),
                    insider_ownership_pct=self._float(row.get("insider_ownership_pct")),
                    institutional_ownership_pct=self._float(row.get("institutional_ownership_pct")),
                    analyst_revision_score=self._float(row.get("analyst_revision_score")),
                    earnings_date=self._date(row.get("earnings_date")),
                    data_quality=quality,
                )
                quality_score = self._quality_score(metrics)
                growth_score = self._growth_score(metrics)
                profitability_score = self._profitability_score(metrics)
                balance_sheet_score = self._balance_sheet_score(metrics)
                valuation_score = self._valuation_score(metrics)
                ownership_score = self._ownership_score(metrics)
                overall = clamp(
                    0.20 * quality_score
                    + 0.20 * growth_score
                    + 0.25 * profitability_score
                    + 0.15 * balance_sheet_score
                    + 0.12 * valuation_score
                    + 0.08 * ownership_score
                )
                context = FundamentalContext(
                    symbol=symbol,
                    profile=profile,
                    metrics=metrics,
                    quality_score=round(quality_score, 2),
                    growth_score=round(growth_score, 2),
                    profitability_score=round(profitability_score, 2),
                    balance_sheet_score=round(balance_sheet_score, 2),
                    valuation_score=round(valuation_score, 2),
                    ownership_score=round(ownership_score, 2),
                    overall_score=round(overall, 2),
                    classification=self._classification(overall),
                    data_quality=quality,
                )
                context.reasons = self._reasons(context)
                context.risks = self._risks(context)
                context.missing_fields = self._missing(metrics)
                records[symbol] = context
        return records

    @staticmethod
    def _clean(value: str | None) -> Optional[str]:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @staticmethod
    def _float(value: str | None) -> Optional[float]:
        if value is None or str(value).strip() == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _date(value: str | None) -> Optional[date]:
        if value is None or str(value).strip() == "":
            return None
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None

    def _growth_score(self, m: FundamentalMetrics) -> float:
        values = [v for v in [m.revenue_growth_yoy_pct, m.eps_growth_yoy_pct] if v is not None]
        if not values:
            return 50
        return clamp(50 + 1.7 * (sum(values) / len(values)))

    def _profitability_score(self, m: FundamentalMetrics) -> float:
        values = []
        if m.gross_margin_pct is not None:
            values.append(45 + 0.65 * m.gross_margin_pct)
        if m.operating_margin_pct is not None:
            values.append(50 + 1.15 * m.operating_margin_pct)
        if m.net_margin_pct is not None:
            values.append(50 + 1.25 * m.net_margin_pct)
        if m.roe_pct is not None:
            values.append(50 + 1.15 * m.roe_pct)
        if m.roic_pct is not None:
            values.append(50 + 1.40 * m.roic_pct)
        if m.free_cash_flow_yield_pct is not None:
            values.append(55 + 2.0 * m.free_cash_flow_yield_pct)
        return clamp(sum(values) / len(values)) if values else 50

    def _balance_sheet_score(self, m: FundamentalMetrics) -> float:
        score = 65.0
        if m.debt_to_equity is not None:
            if m.debt_to_equity <= 0.5:
                score += 18
            elif m.debt_to_equity <= 1.0:
                score += 8
            elif m.debt_to_equity > 2.0:
                score -= 22
            else:
                score -= 8
        return clamp(score)

    def _valuation_score(self, m: FundamentalMetrics) -> float:
        score = 60.0
        if m.peg_ratio is not None:
            if m.peg_ratio <= 1.5:
                score += 18
            elif m.peg_ratio <= 2.5:
                score += 4
            elif m.peg_ratio > 4:
                score -= 18
            else:
                score -= 8
        if m.forward_pe is not None:
            if m.forward_pe <= 25:
                score += 12
            elif m.forward_pe <= 40:
                score += 2
            elif m.forward_pe > 70:
                score -= 18
            else:
                score -= 8
        return clamp(score)

    def _ownership_score(self, m: FundamentalMetrics) -> float:
        score = 55.0
        if m.insider_ownership_pct is not None:
            score += min(15, m.insider_ownership_pct * 1.2)
        if m.institutional_ownership_pct is not None:
            if m.institutional_ownership_pct >= 55:
                score += 10
            elif m.institutional_ownership_pct < 20:
                score -= 8
        if m.analyst_revision_score is not None:
            score = 0.70 * score + 0.30 * m.analyst_revision_score
        return clamp(score)

    def _quality_score(self, m: FundamentalMetrics) -> float:
        score = 60.0
        if m.market_cap_usd is not None:
            if m.market_cap_usd >= 200_000_000_000:
                score += 24
            elif m.market_cap_usd >= 50_000_000_000:
                score += 10
            elif m.market_cap_usd < 10_000_000_000:
                score -= 14
        if m.beta is not None:
            if m.beta <= 1.2:
                score += 8
            elif m.beta > 1.6:
                score -= 10
        return clamp(score)

    @staticmethod
    def _classification(score: float) -> str:
        if score >= 85:
            return "atlas_quality_leader"
        if score >= 75:
            return "quality_candidate"
        if score >= 65:
            return "acceptable"
        if score >= 55:
            return "watch_only"
        return "fundamental_weakness"

    @staticmethod
    def _reasons(context: FundamentalContext) -> list[str]:
        m = context.metrics
        reasons = []
        if context.quality_score >= 78:
            reasons.append("Large, liquid security with strong quality profile.")
        if context.growth_score >= 75:
            reasons.append("Growth metrics are above Atlas baseline.")
        if context.profitability_score >= 80:
            reasons.append("Margins/returns indicate strong profitability.")
        if context.balance_sheet_score >= 75:
            reasons.append("Balance sheet risk appears controlled in sample data.")
        if context.valuation_score >= 70:
            reasons.append("Valuation is acceptable relative to growth/quality.")
        if m and m.analyst_revision_score and m.analyst_revision_score >= 75:
            reasons.append("Analyst revision score is supportive.")
        return reasons or ["Fundamental context is present but does not show standout strengths."]

    @staticmethod
    def _risks(context: FundamentalContext) -> list[str]:
        m = context.metrics
        risks = []
        if context.valuation_score < 55:
            risks.append("Valuation score is weak; avoid chasing extended entries.")
        if context.growth_score < 55:
            risks.append("Growth score is below Atlas preference.")
        if m and m.debt_to_equity is not None and m.debt_to_equity > 1.5:
            risks.append("Debt/equity is elevated in sample data.")
        if m and m.beta is not None and m.beta > 1.6:
            risks.append(f"Beta is high at {m.beta:.2f}; position sizing should be conservative.")
        return risks

    @staticmethod
    def _missing(m: FundamentalMetrics) -> list[str]:
        fields = [
            "market_cap_usd",
            "forward_pe",
            "peg_ratio",
            "revenue_growth_yoy_pct",
            "operating_margin_pct",
            "roe_pct",
            "roic_pct",
            "debt_to_equity",
            "analyst_revision_score",
        ]
        return [field for field in fields if getattr(m, field) is None]
