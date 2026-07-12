from __future__ import annotations

from atlas_core.enums import MarketRegime, Verdict


def verdict_from_score(score: float, portfolio_fit_score: float, market_regime: MarketRegime) -> Verdict:
    if portfolio_fit_score < 65 and score >= 82:
        return Verdict.GOOD_ASSET_BAD_FIT
    if market_regime == MarketRegime.RISK_OFF and score >= 90:
        return Verdict.SWING_CANDIDATE
    if score >= 90:
        return Verdict.STRONG_BUY
    if score >= 82:
        return Verdict.BUY
    if score >= 72:
        return Verdict.WATCH
    return Verdict.AVOID
