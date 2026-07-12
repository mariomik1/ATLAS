from __future__ import annotations

from collections import defaultdict
from datetime import date

from atlas_core.enums import AssetClass
from atlas_core.models import PortfolioPosition, PortfolioSnapshot


TECH_SECTORS = {"technology", "software", "semiconductors", "cybersecurity", "nasdaq income", "information technology"}
AI_THEMES = {"ai", "artificial intelligence", "semiconductors", "cloud", "cybersecurity"}


class PortfolioEngine:
    """Portfolio engine v1 for Atlas technical MVP.

    This engine remains advisory-only. It calculates exposures and produces
    warnings/actions; it never submits orders or changes holdings.
    """

    def __init__(self, portfolio_config: dict):
        self.portfolio_config = portfolio_config
        self.constraints = portfolio_config.get("constraints", {})
        self.targets = portfolio_config.get("targets", {})

    def snapshot(self) -> PortfolioSnapshot:
        positions = [
            PortfolioPosition(
                symbol=row["symbol"],
                name=row["name"],
                asset_class=AssetClass(row.get("asset_class", "stock")),
                sector=row.get("sector"),
                market_value_eur=float(row.get("market_value_eur", 0)),
                intent=row.get("intent"),
                theme=row.get("theme"),
                liquidity=row.get("liquidity", "liquid"),
            )
            for row in self.portfolio_config.get("positions", [])
        ]
        cash = self.portfolio_config.get("cash", {})
        satellite = self.portfolio_config.get("satellite", {})
        snapshot = PortfolioSnapshot(
            owner=self.portfolio_config.get("owner", "Mario"),
            base_currency=self.portfolio_config.get("base_currency", "EUR"),
            as_of=date.fromisoformat(str(self.portfolio_config.get("as_of", date.today()))),
            cash_eur=float(cash.get("amount_eur", 0)),
            cash_interest_rate_pct=float(cash.get("average_interest_rate_pct", 0)),
            positions=positions,
            satellite_max_eur=float(satellite.get("max_capital_eur", self.constraints.get("max_satellite_capital_eur", 50000))),
            target_cash_min_eur=float(self.targets.get("cash_min_eur", 50000)),
            target_cash_max_eur=float(self.targets.get("cash_max_eur", 90000)),
            target_allocations={str(k): float(v) for k, v in self.targets.get("allocation_pct", {}).items()},
        )
        exposures = self._calculate_exposures(snapshot)
        snapshot.exposure_by_asset_class = exposures["asset_class"]
        snapshot.exposure_by_sector = exposures["sector"]
        snapshot.exposure_by_theme = exposures["theme"]
        snapshot.risk_flags = self.risk_flags(snapshot)
        snapshot.advisory_actions = self.advisory_actions(snapshot)
        return snapshot

    def _calculate_exposures(self, snapshot: PortfolioSnapshot) -> dict[str, dict[str, float]]:
        total = snapshot.total_tracked_eur or 1.0
        asset_class = defaultdict(float)
        sector = defaultdict(float)
        theme = defaultdict(float)
        asset_class["cash"] += snapshot.cash_eur
        for pos in snapshot.positions:
            asset_class[str(pos.asset_class)] += pos.market_value_eur
            if pos.sector:
                sector[pos.sector] += pos.market_value_eur
            if pos.theme:
                theme[pos.theme] += pos.market_value_eur
            if pos.sector and pos.sector.lower() in TECH_SECTORS:
                theme["tech_ai_proxy"] += pos.market_value_eur
            if pos.theme and pos.theme.lower() in AI_THEMES:
                theme["tech_ai_proxy"] += pos.market_value_eur
        return {
            "asset_class": {k: round(v / total * 100, 2) for k, v in sorted(asset_class.items())},
            "sector": {k: round(v / total * 100, 2) for k, v in sorted(sector.items())},
            "theme": {k: round(v / total * 100, 2) for k, v in sorted(theme.items())},
        }

    def risk_flags(self, snapshot: PortfolioSnapshot) -> list[str]:
        flags: list[str] = []
        if snapshot.cash_eur > snapshot.target_cash_max_eur:
            flags.append(f"Cash is above target range by EUR {snapshot.cash_eur - snapshot.target_cash_max_eur:,.0f}.")
        if snapshot.cash_eur < snapshot.target_cash_min_eur:
            flags.append("Cash is below target liquidity range; avoid forced deployment.")
        tech_ai = snapshot.exposure_by_theme.get("tech_ai_proxy", 0)
        max_tech_ai = float(self.constraints.get("max_tech_ai_exposure_pct", 35))
        if tech_ai > max_tech_ai:
            flags.append(f"Tech/AI proxy exposure is high at {tech_ai:.1f}% versus {max_tech_ai:.1f}% guideline.")
        satellite_allocated = float(self.portfolio_config.get("satellite", {}).get("allocated_capital_eur", 0))
        if satellite_allocated > snapshot.satellite_max_eur:
            flags.append("Satellite capital exceeds configured maximum.")
        return flags

    def advisory_actions(self, snapshot: PortfolioSnapshot) -> list[str]:
        actions: list[str] = []
        if snapshot.cash_eur > snapshot.target_cash_max_eur:
            deployable = max(0.0, snapshot.cash_eur - snapshot.target_cash_max_eur)
            actions.append(
                f"Cash above target range. Advisory only: evaluate staged deployment of up to EUR {deployable:,.0f} into Core ETF, real-estate reserve or high-conviction opportunities."
            )
        else:
            actions.append("Cash is within or below configured target range; no forced deployment required.")
        actions.append(f"Satellite risk budget capped at EUR {snapshot.satellite_max_eur:,.0f}.")
        for flag in snapshot.risk_flags[:3]:
            actions.append(f"Portfolio warning: {flag}")
        return actions

    def exposure_after_trade(self, snapshot: PortfolioSnapshot, sector: str | None, theme: str | None, trade_value_eur: float) -> dict[str, float]:
        total = max(snapshot.total_tracked_eur + trade_value_eur, 1.0)
        result: dict[str, float] = {}
        if sector:
            current = snapshot.exposure_by_sector.get(sector, 0) / 100 * snapshot.total_tracked_eur
            result[f"sector:{sector}"] = round((current + trade_value_eur) / total * 100, 2)
        if theme:
            current = snapshot.exposure_by_theme.get(theme, 0) / 100 * snapshot.total_tracked_eur
            result[f"theme:{theme}"] = round((current + trade_value_eur) / total * 100, 2)
        return result
