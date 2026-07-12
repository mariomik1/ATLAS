from __future__ import annotations

from atlas_core.enums import MarketRegime
from atlas_core.models import FactorScore, MarketSnapshot, PortfolioFit, PortfolioSnapshot, TradePlan
from atlas_core.providers.base import AssetMarketData


class RiskEngine:
    def __init__(self, risk_rules: dict):
        self.risk_rules = risk_rules

    def evaluate(self, item: AssetMarketData, weight: float) -> FactorScore:
        score = 85
        risks = []
        reasons = ["Risk score uses ATR proxy, configured risk budget and market-regime multiplier."]
        if item.atr_pct > 4.5:
            score -= 15
            risks.append("High volatility; position size should be reduced or actively managed.")
        if item.atr_pct < 2.0:
            score += 4
            reasons.append("Low ATR supports cleaner risk definition.")
        return FactorScore(
            name="risk",
            score=max(0, min(100, score)),
            weight=weight,
            reasons=reasons,
            risks=risks,
            data_quality=item.data_quality,
        )

    def portfolio_fit(
        self,
        item: AssetMarketData,
        market: MarketRegime | MarketSnapshot,
        trade_plan: TradePlan,
        portfolio: PortfolioSnapshot | None = None,
    ) -> PortfolioFit:
        market_regime = market.regime if isinstance(market, MarketSnapshot) else market
        market_multiplier = market.position_size_multiplier if isinstance(market, MarketSnapshot) else 1.0
        max_default = float(self.risk_rules.get("satellite", {}).get("default_max_position_eur", 10000))
        warnings: list[str] = []
        notes: list[str] = []
        score = 82.0
        classification = "acceptable"

        if item.asset.sector in {"Semiconductors", "Software", "Cybersecurity", "Technology"}:
            warnings.append("Technology/AI exposure must be checked against current portfolio before execution.")
            score -= 8

        exposure_after_trade: dict[str, float] = {}
        suggested_offsets: list[str] = []
        if portfolio is not None:
            total_after = max(portfolio.total_tracked_eur + max_default, 1.0)
            if item.asset.sector:
                current_sector_value = portfolio.exposure_by_sector.get(item.asset.sector, 0) / 100 * portfolio.total_tracked_eur
                sector_after = (current_sector_value + max_default) / total_after * 100
                exposure_after_trade[f"sector:{item.asset.sector}"] = round(sector_after, 2)
                if sector_after > float(self.risk_rules.get("portfolio", {}).get("max_single_sector_pct", 35)):
                    warnings.append(f"Sector exposure after trade could exceed guideline ({sector_after:.1f}%).")
                    score -= 8
                    suggested_offsets.append("Consider reducing overlapping ETF/theme exposure or using this only as a short swing trade.")
            if item.asset.theme:
                current_theme_value = portfolio.exposure_by_theme.get(item.asset.theme, 0) / 100 * portfolio.total_tracked_eur
                theme_after = (current_theme_value + max_default) / total_after * 100
                exposure_after_trade[f"theme:{item.asset.theme}"] = round(theme_after, 2)

        if market_regime == MarketRegime.NEUTRAL:
            warnings.append("Market regime is Neutral; Atlas uses reduced position sizing.")
            score -= 6
            classification = "selective_reduced_size"
        elif market_regime == MarketRegime.RISK_OFF:
            warnings.append("Market regime is Risk-Off; use reduced position size or wait.")
            score -= 18
            classification = "reduced_size_only"

        if item.atr_pct > 4.5:
            max_default *= 0.75
            classification = "swing_only"
            notes.append("High ATR suggests using only tactical swing exposure.")

        risk_per_share = max(trade_plan.entry_high - trade_plan.stop_loss, 0.01)
        satellite_max = float(self.risk_rules.get("satellite", {}).get("max_capital_eur", 50000))
        risk_pct = float(self.risk_rules.get("risk_per_trade", {}).get("medium_vol_pct_of_satellite", 1.0)) / 100
        risk_budget = satellite_max * risk_pct * market_multiplier
        default_cap = max_default * market_multiplier
        estimated_shares = risk_budget / risk_per_share
        estimated_position = min(default_cap, estimated_shares * trade_plan.entry_high)
        notes.append(
            f"Position cap uses risk budget, default cap and market multiplier {market_multiplier:.2f}: EUR {estimated_position:,.0f}."
        )
        if market_multiplier < 1.0:
            notes.append("Market regime reduced the maximum position size.")
        return PortfolioFit(
            score=round(max(0, min(100, score)), 2),
            classification=classification,
            max_position_eur=round(max(0, estimated_position), 2),
            advisory_notes=notes,
            warnings=warnings,
            exposure_after_trade=exposure_after_trade,
            suggested_offset_actions=suggested_offsets,
        )
