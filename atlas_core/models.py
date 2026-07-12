from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from atlas_core.enums import AssetClass, DataQualityLevel, InvestmentIntent, MarketRegime, Strategy, Verdict
from atlas_core.utils.time_utils import utc_now


class DataQuality(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    level: DataQualityLevel = DataQualityLevel.SAMPLE
    provider: str = "manual_sample"
    as_of: datetime = Field(default_factory=utc_now)
    issues: List[str] = Field(default_factory=list)


class Asset(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    name: str
    asset_class: AssetClass
    sector: Optional[str] = None
    theme: Optional[str] = None
    currency: str = "USD"
    isin: Optional[str] = None
    wkn: Optional[str] = None


class CompanyProfile(BaseModel):
    """Stable company/security profile used by the fundamentals and search layers."""

    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    name: str
    asset_class: AssetClass
    sector: Optional[str] = None
    industry: Optional[str] = None
    theme: Optional[str] = None
    country: Optional[str] = None
    exchange: Optional[str] = None
    currency: str = "USD"
    isin: Optional[str] = None
    wkn: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    data_quality: DataQuality = Field(default_factory=DataQuality)


class FundamentalMetrics(BaseModel):
    """Normalized fundamental metrics. Missing values are allowed and penalized by the engine."""

    symbol: str
    market_cap_usd: Optional[float] = Field(default=None, ge=0)
    revenue_growth_yoy_pct: Optional[float] = None
    eps_growth_yoy_pct: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    operating_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    roe_pct: Optional[float] = None
    roic_pct: Optional[float] = None
    debt_to_equity: Optional[float] = Field(default=None, ge=0)
    free_cash_flow_yield_pct: Optional[float] = None
    pe_ttm: Optional[float] = Field(default=None, ge=0)
    forward_pe: Optional[float] = Field(default=None, ge=0)
    peg_ratio: Optional[float] = Field(default=None, ge=0)
    dividend_yield_pct: Optional[float] = Field(default=None, ge=0)
    beta: Optional[float] = Field(default=None, ge=0)
    insider_ownership_pct: Optional[float] = Field(default=None, ge=0, le=100)
    institutional_ownership_pct: Optional[float] = Field(default=None, ge=0, le=100)
    analyst_revision_score: Optional[float] = Field(default=None, ge=0, le=100)
    earnings_date: Optional[date] = None
    data_quality: DataQuality = Field(default_factory=DataQuality)


class FundamentalContext(BaseModel):
    """Explainable fundamental score and its sub-components."""

    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    profile: Optional[CompanyProfile] = None
    metrics: Optional[FundamentalMetrics] = None
    quality_score: float = Field(default=50, ge=0, le=100)
    growth_score: float = Field(default=50, ge=0, le=100)
    profitability_score: float = Field(default=50, ge=0, le=100)
    balance_sheet_score: float = Field(default=50, ge=0, le=100)
    valuation_score: float = Field(default=50, ge=0, le=100)
    ownership_score: float = Field(default=50, ge=0, le=100)
    overall_score: float = Field(default=50, ge=0, le=100)
    classification: str = "unknown"
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class IdentifierMatch(BaseModel):
    """Normalized identifier/search match for ticker, name, ISIN, WKN or aliases."""

    model_config = ConfigDict(use_enum_values=True)
    query: str
    symbol: str
    name: str
    asset_class: AssetClass
    match_type: str = "symbol"  # symbol | name | isin | wkn | alias | partial | provider
    confidence: float = Field(default=100, ge=0, le=100)
    exchange: Optional[str] = None
    country: Optional[str] = None
    currency: str = "USD"
    isin: Optional[str] = None
    wkn: Optional[str] = None
    figi: Optional[str] = None
    provider: str = "csv_sample"
    data_quality: DataQuality = Field(default_factory=DataQuality)


class SearchResult(BaseModel):
    """Search response used by Atlas Screener/Search."""

    query: str
    matches: List[IdentifierMatch] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class OhlcvBar(BaseModel):
    """Normalized daily or intraday OHLCV record used by chart engines.

    Sprint 2+ uses daily sample history. Future providers must map live/delayed
    API payloads into this model before any engine uses them.
    """

    symbol: str
    date: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: int = Field(ge=0)
    source: str = "csv_sample"


class ChartContext(BaseModel):
    """Asset-level technical context calculated from OHLCV history."""

    symbol: str
    current_price: float = Field(gt=0)
    ema_20: Optional[float] = Field(default=None, gt=0)
    ema_50: Optional[float] = Field(default=None, gt=0)
    sma_200: Optional[float] = Field(default=None, gt=0)
    rsi_14: Optional[float] = Field(default=None, ge=0, le=100)
    atr_14: Optional[float] = Field(default=None, ge=0)
    atr_pct: Optional[float] = Field(default=None, ge=0)
    return_20d_pct: Optional[float] = None
    return_60d_pct: Optional[float] = None
    distance_to_ema_20_pct: Optional[float] = None
    distance_to_ema_50_pct: Optional[float] = None
    distance_to_sma_200_pct: Optional[float] = None
    swing_low_20: Optional[float] = Field(default=None, gt=0)
    swing_high_20: Optional[float] = Field(default=None, gt=0)
    support_1: Optional[float] = Field(default=None, gt=0)
    support_2: Optional[float] = Field(default=None, gt=0)
    resistance_1: Optional[float] = Field(default=None, gt=0)
    resistance_2: Optional[float] = Field(default=None, gt=0)
    volume_ratio_20d: Optional[float] = Field(default=None, ge=0)
    trend_status: str = "unknown"
    market_structure: str = "unknown"
    setup_type: str = "unknown"
    score: float = Field(default=50, ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class NewsItem(BaseModel):
    """Normalized finance-news item used by the Sprint 3 Catalyst Engine."""

    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    title: str
    summary: str = ""
    source: str = "sample"
    url: Optional[str] = None
    published_at: datetime = Field(default_factory=utc_now)
    category: str = "company"
    event_type: str = "news"
    sentiment_score: float = Field(default=0.0, ge=-1, le=1)
    relevance_score: float = Field(default=50, ge=0, le=100)
    impact_score: float = Field(default=50, ge=0, le=100)
    risk_flag: bool = False
    topics: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class CatalystEvent(BaseModel):
    """Known upcoming or recent event that may explain or affect a setup."""

    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    event_type: str
    event_date: date
    description: str
    importance: str = "medium"  # low | medium | high
    source: str = "sample"
    data_quality: DataQuality = Field(default_factory=DataQuality)


class CatalystContext(BaseModel):
    """News, event and catalyst context used by daily recommendations."""

    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    score: float = Field(default=50, ge=0, le=100)
    news_count: int = Field(default=0, ge=0)
    average_sentiment: Optional[float] = Field(default=None, ge=-1, le=1)
    average_relevance: Optional[float] = Field(default=None, ge=0, le=100)
    average_impact: Optional[float] = Field(default=None, ge=0, le=100)
    primary_catalyst: Optional[str] = None
    catalyst_type: str = "none"  # positive | neutral | negative | mixed | none
    event_types: List[str] = Field(default_factory=list)
    upcoming_events: List[CatalystEvent] = Field(default_factory=list)
    news: List[NewsItem] = Field(default_factory=list)
    positive_count: int = Field(default=0, ge=0)
    negative_count: int = Field(default=0, ge=0)
    risk_flag_count: int = Field(default=0, ge=0)
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class MarketIndicator(BaseModel):
    """Technical market signal for a benchmark or risk indicator."""

    symbol: str
    name: str
    close: float = Field(gt=0)
    sma_50: Optional[float] = Field(default=None, gt=0)
    sma_200: Optional[float] = Field(default=None, gt=0)
    return_20d_pct: Optional[float] = None
    return_60d_pct: Optional[float] = None
    distance_to_sma_50_pct: Optional[float] = None
    distance_to_sma_200_pct: Optional[float] = None
    rsi_14: Optional[float] = Field(default=None, ge=0, le=100)
    trend_status: str = "unknown"
    score: float = Field(default=50, ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    regime: MarketRegime
    score: float = Field(ge=0, le=100)
    summary: str
    as_of: datetime = Field(default_factory=utc_now)
    data_quality: DataQuality = Field(default_factory=DataQuality)
    indicators: List[MarketIndicator] = Field(default_factory=list)
    component_scores: Dict[str, float] = Field(default_factory=dict)
    trade_permission: str = "normal"
    position_size_multiplier: float = Field(default=1.0, ge=0, le=1.5)
    warnings: List[str] = Field(default_factory=list)


class FactorScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0)
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class ScoreBreakdown(BaseModel):
    total_score: float = Field(ge=0, le=100)
    factors: List[FactorScore]
    confidence_pct: float = Field(ge=0, le=100)

    def as_dict_by_factor(self) -> Dict[str, float]:
        return {factor.name: factor.score for factor in self.factors}


class TradePlan(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    currency: str = "USD"
    strategy: Strategy
    current_price: float = Field(gt=0)
    entry_low: float = Field(gt=0)
    entry_high: float = Field(gt=0)
    do_not_chase_above: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit_1: float = Field(gt=0)
    take_profit_2: Optional[float] = Field(default=None, gt=0)
    take_profit_3: Optional[float] = Field(default=None, gt=0)
    reward_risk_ratio: float = Field(ge=0)
    holding_period: str
    notes: List[str] = Field(default_factory=list)


class PortfolioFit(BaseModel):
    score: float = Field(ge=0, le=100)
    classification: str
    max_position_eur: float = Field(ge=0)
    advisory_notes: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    exposure_after_trade: Dict[str, float] = Field(default_factory=dict)
    suggested_offset_actions: List[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    asset: Asset
    intent: InvestmentIntent
    verdict: Verdict
    strategy: Strategy
    atlas_score: float = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    market_snapshot: MarketSnapshot
    portfolio_fit: PortfolioFit
    trade_plan: Optional[TradePlan] = None
    chart_context: Optional[ChartContext] = None
    catalyst_context: Optional[CatalystContext] = None
    fundamental_context: Optional[FundamentalContext] = None
    identifier_match: Optional[IdentifierMatch] = None
    key_reasons: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    ai_statement: str
    back_book_summary: Dict[str, Any] = Field(default_factory=dict)
    data_quality: DataQuality = Field(default_factory=DataQuality)
    created_at: datetime = Field(default_factory=utc_now)


class PortfolioPosition(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    name: str
    asset_class: AssetClass
    sector: Optional[str] = None
    theme: Optional[str] = None
    market_value_eur: float = Field(ge=0)
    intent: Optional[str] = None


class PortfolioExposure(BaseModel):
    name: str
    value_eur: float = Field(ge=0)
    pct_of_total: float = Field(ge=0, le=100)


class PortfolioAlert(BaseModel):
    severity: str = "info"  # info | warning | critical
    area: str
    message: str
    suggested_action: Optional[str] = None


class PortfolioSnapshot(BaseModel):
    owner: str
    base_currency: str = "EUR"
    as_of: date
    cash_eur: float = Field(ge=0)
    cash_interest_rate_pct: float = Field(ge=0)
    positions: List[PortfolioPosition] = Field(default_factory=list)
    satellite_max_eur: float = Field(ge=0)
    satellite_allocated_eur: float = Field(default=0, ge=0)
    cash_target_min_eur: float = Field(default=0, ge=0)
    cash_target_max_eur: float = Field(default=0, ge=0)
    asset_allocation: Dict[str, PortfolioExposure] = Field(default_factory=dict)
    sector_exposure: Dict[str, PortfolioExposure] = Field(default_factory=dict)
    tech_ai_exposure_eur: float = Field(default=0, ge=0)
    tech_ai_exposure_pct: float = Field(default=0, ge=0, le=100)
    alerts: List[PortfolioAlert] = Field(default_factory=list)
    # Technical MVP compatibility/explainability fields used by Portfolio Engine v1.
    target_cash_min_eur: float = Field(default=50000, ge=0)
    target_cash_max_eur: float = Field(default=90000, ge=0)
    target_allocations: Dict[str, float] = Field(default_factory=dict)
    exposure_by_asset_class: Dict[str, float] = Field(default_factory=dict)
    exposure_by_sector: Dict[str, float] = Field(default_factory=dict)
    exposure_by_theme: Dict[str, float] = Field(default_factory=dict)
    risk_flags: List[str] = Field(default_factory=list)
    advisory_actions: List[str] = Field(default_factory=list)

    @property
    def invested_eur(self) -> float:
        return sum(position.market_value_eur for position in self.positions)

    @property
    def total_tracked_eur(self) -> float:
        return self.cash_eur + self.invested_eur

    @property
    def cash_pct(self) -> float:
        total = self.total_tracked_eur
        return 0 if total <= 0 else round(self.cash_eur / total * 100, 2)

    @property
    def satellite_usage_pct(self) -> float:
        return 0 if self.satellite_max_eur <= 0 else round(self.satellite_allocated_eur / self.satellite_max_eur * 100, 2)


class FireSnapshot(BaseModel):
    status: str
    progress_pct: float = Field(ge=0, le=100)
    target_monthly_cashflow_eur: float = Field(ge=0)
    projected_year: int
    message: str
    target_capital_eur: float = Field(default=1_200_000, ge=0)
    current_capital_eur: float = Field(default=0, ge=0)
    monthly_contribution_eur: float = Field(default=0, ge=0)
    expected_return_pct: float = Field(default=5.0, ge=-100, le=100)
    years_to_target: Optional[float] = Field(default=None, ge=0)
    probability_pct: Optional[float] = Field(default=None, ge=0, le=100)
    scenario: Dict[str, Any] = Field(default_factory=dict)
    target_capital_eur: float = Field(default=1_200_000, ge=0)
    current_capital_eur: float = Field(default=0, ge=0)
    gap_to_target_eur: float = Field(default=0, ge=0)
    annual_savings_eur: float = Field(default=0, ge=0)
    expected_nominal_return_pct: float = Field(default=0, ge=0)
    safe_withdrawal_rate_pct: float = Field(default=3.5, ge=0)
    fire_probability_pct: float = Field(default=50, ge=0, le=100)
    scenario: Dict[str, Any] = Field(default_factory=dict)


class DailyBriefing(BaseModel):
    app_name: str = "Atlas"
    as_of: datetime = Field(default_factory=utc_now)
    market: MarketSnapshot
    portfolio: PortfolioSnapshot
    fire: FireSnapshot
    market_catalysts: Optional[CatalystContext] = None
    headline: str
    no_trade_message: Optional[str] = None
    recommendations: List[Recommendation]
    actions: List[str] = Field(default_factory=list)
    executive_summary: List[str] = Field(default_factory=list)
    data_quality_notes: List[str] = Field(default_factory=list)
    technical_mvp_version: str = "technical_mvp_0.1"
