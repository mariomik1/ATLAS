from __future__ import annotations

from datetime import date

from atlas_core.models import FireSnapshot, PortfolioSnapshot


class FireEngine:
    """FIRE Engine v1.

    This remains a planning model, not a promise. It turns portfolio state and
    configured assumptions into directional progress, gap and scenario values.
    """

    def __init__(self, portfolio_config: dict | None = None):
        self.portfolio_config = portfolio_config or {}
        self.fire_config = self.portfolio_config.get("fire", {})

    def build_snapshot(self, portfolio: PortfolioSnapshot) -> FireSnapshot:
        target_monthly = float(self.fire_config.get("target_monthly_cashflow_eur", 3500))
        safe_withdrawal_rate = float(self.fire_config.get("safe_withdrawal_rate_pct", 3.5))
        target_capital = float(
            self.fire_config.get("target_capital_eur")
            or (target_monthly * 12 / max(safe_withdrawal_rate / 100, 0.001))
        )
        annual_savings = float(self.fire_config.get("annual_savings_eur", 60000))
        expected_return = float(self.fire_config.get("expected_nominal_return_pct", 5.0))
        current = portfolio.total_tracked_eur
        progress = min(100.0, current / target_capital * 100) if target_capital else 0.0
        gap = max(0.0, target_capital - current)
        years_to_target = self._years_to_target(current, target_capital, annual_savings, expected_return)
        current_year = date.today().year
        projected_year = int(current_year + round(years_to_target)) if years_to_target is not None else 2037
        probability = self._probability(progress, portfolio, expected_return)
        status = "achieved" if progress >= 100 else "on_track" if probability >= 70 else "build_phase"
        scenario = {
            "base_case_years_to_target": years_to_target,
            "annual_savings_eur": annual_savings,
            "expected_nominal_return_pct": expected_return,
            "safe_withdrawal_rate_pct": safe_withdrawal_rate,
            "current_cash_pct": portfolio.cash_pct,
            "tech_ai_exposure_pct": portfolio.tech_ai_exposure_pct,
        }
        message = (
            f"FIRE Engine v1: EUR {current:,.0f} tracked versus EUR {target_capital:,.0f} target; "
            f"projected target year {projected_year} under configured assumptions."
        )
        return FireSnapshot(
            status=status,
            progress_pct=round(progress, 2),
            target_monthly_cashflow_eur=target_monthly,
            projected_year=projected_year,
            message=message,
            target_capital_eur=round(target_capital, 2),
            current_capital_eur=round(current, 2),
            gap_to_target_eur=round(gap, 2),
            annual_savings_eur=annual_savings,
            expected_nominal_return_pct=expected_return,
            safe_withdrawal_rate_pct=safe_withdrawal_rate,
            fire_probability_pct=probability,
            scenario=scenario,
        )

    @staticmethod
    def _years_to_target(current: float, target: float, annual_savings: float, expected_return_pct: float) -> float | None:
        if current >= target:
            return 0.0
        r = max(expected_return_pct / 100, 0.0)
        value = current
        for year in range(1, 61):
            value = value * (1 + r) + annual_savings
            if value >= target:
                # rough fractional interpolation from previous year
                previous = (value - annual_savings) / (1 + r) if (1 + r) else current
                annual_gain = value - previous
                fraction = 1.0 if annual_gain <= 0 else max(0.0, min(1.0, (target - previous) / annual_gain))
                return round((year - 1) + fraction, 2)
        return None

    @staticmethod
    def _probability(progress: float, portfolio: PortfolioSnapshot, expected_return_pct: float) -> float:
        score = 35 + progress * 0.55
        if portfolio.cash_eur > portfolio.cash_target_max_eur > 0:
            score -= min(10, (portfolio.cash_eur - portfolio.cash_target_max_eur) / 10000)
        if portfolio.tech_ai_exposure_pct > 28:
            score -= min(8, (portfolio.tech_ai_exposure_pct - 28) * 0.6)
        if expected_return_pct >= 4:
            score += 5
        return round(max(0, min(100, score)), 1)
