# ATLAS SPEC

**Version:** 0.1
**Status:** Implementation Baseline / MVP Specification
**Owner:** Mario Mikikits
**Project:** Atlas - Personal Wealth Operating System
**Last updated:** 2026-07-05
**Classification:** Personal / Internal
**Source baseline:** ATLAS_BIBLE_v0.2_PRO.md

---

## 0. Document Purpose

This document translates the Atlas Bible into an implementation-ready product and engineering specification.

The Atlas Bible defines the durable philosophy: why Atlas exists, what it optimizes, and which principles must not be violated casually.

This Atlas Spec defines the first executable version: screens, components, data models, engine interfaces, repository structure, configuration, MVP tickets, acceptance criteria, testing plan, and coding-agent prompts.

### 0.1 Scope of this spec

This v0.1 spec covers:

- Streamlit MVP architecture;
- local-first execution model;
- initial data provider abstraction;
- Mission Control page;
- Daily Candidates page;
- Screener/Search page;
- Candidate Back-Book page;
- manual portfolio input;
- Atlas Score implementation v0.1;
- Strategy Engine v0.1;
- Chart Engine v0.1;
- Trade Plan Engine v0.1;
- Risk Engine v0.1;
- Portfolio Fit v0.1;
- AI Statement placeholder;
- journal-ready recommendation tracking;
- first Claude/Coding-Agent tickets.

### 0.2 Non-scope of this spec

This version does not define:

- broker integration;
- automated trading;
- tax optimization;
- full real estate scoring;
- paid-data provider contract decisions;
- production authentication;
- full React/Next.js UI;
- push notifications;
- multi-user SaaS architecture;
- financial advice automation.

Atlas remains a decision support system. Human review and approval are mandatory.

---

# 1. Product Definition

## 1.1 Product name

**Atlas**

Working interpretation:

> Atlas is a personal Wealth Operating System that helps Mario decide what to do with capital today: invest, wait, rebalance, research, reduce risk, or do nothing.

## 1.2 MVP objective

The MVP must prove one thing:

> Atlas can create useful, explainable daily decision plans from market data, watchlists, chart analysis, scoring rules, and portfolio context.

The MVP does not need a perfect design. It must produce clear, structured, testable recommendations.

## 1.3 Primary user outcome

When Mario opens Atlas in the morning, he should know within 30 seconds:

1. What is the current market regime?
2. Are there attractive opportunities today?
3. What are the top candidates?
4. What is the strategy for each candidate?
5. Where would Atlas enter?
6. Where is the stop-loss?
7. Where are take-profit levels?
8. What is the suggested position size?
9. Is the decision compatible with the portfolio?
10. Is there a reason to do nothing?

## 1.4 MVP success criteria

Atlas MVP is successful if:

- dashboard loads without manual code changes;
- user can update a watchlist in config;
- user sees market regime;
- user sees up to 10 ranked candidates;
- each formal candidate has entry zone, stop-loss, TP1, TP2, CRV, strategy, score and confidence;
- candidates with incomplete trade plan are downgraded automatically;
- user can search a single asset by ticker or name;
- ISIN/WKN are structurally supported, even if provider coverage is partial;
- output is exportable to CSV/JSON;
- data quality is visible;
- no automatic trading is possible;
- recommendations are stored for later review.

---

# 2. Design Principles for Implementation

## 2.1 Build from engines, not screens

Screens should display outputs from engines. They should not contain business logic.

Correct:

```text
ChartEngine -> TradePlanEngine -> Recommendation -> UI Card
```

Wrong:

```text
Streamlit page calculates stop-loss directly
```

## 2.2 Data contracts first

Every engine must input and output structured objects. Loose dictionaries are allowed in the early prototype only when they map to documented schema fields.

## 2.3 Explainability is mandatory

Every score, downgrade, veto, entry zone, stop-loss and take-profit level must include at least one rationale field.

## 2.4 No hidden magic

AI may summarize and explain. AI must not silently invent source data, prices, fundamentals, or chart levels.

## 2.5 Local-first, upgradeable later

The first version should run locally or on Streamlit Cloud. Architecture must remain compatible with a future backend.

## 2.6 MVP is not production

The first version may use:

- local CSV files;
- YAML config;
- JSON exports;
- SQLite optionally;
- simple provider adapters.

But it must avoid irreversible architecture choices.

---

# 3. Recommended Repository Structure

```text
atlas/
├── README.md
├── ATLAS_BIBLE.md
├── ATLAS_SPEC.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── app.py
├── config/
│   ├── settings.yaml
│   ├── watchlists.yaml
│   ├── risk_rules.yaml
│   ├── scoring_weights.yaml
│   └── portfolio.yaml
├── data/
│   ├── cache/
│   ├── exports/
│   ├── journal/
│   └── samples/
├── atlas_core/
│   ├── __init__.py
│   ├── models.py
│   ├── enums.py
│   ├── config_loader.py
│   ├── orchestrator.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── yfinance_provider.py
│   │   ├── finviz_provider.py
│   │   ├── manual_provider.py
│   │   └── identifier_resolver.py
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── market_engine.py
│   │   ├── fundamental_engine.py
│   │   ├── chart_engine.py
│   │   ├── strategy_engine.py
│   │   ├── trade_plan_engine.py
│   │   ├── risk_engine.py
│   │   ├── portfolio_engine.py
│   │   ├── fire_engine.py
│   │   ├── ai_narrative_engine.py
│   │   ├── journal_engine.py
│   │   └── learning_engine.py
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── atlas_score.py
│   │   ├── weights.py
│   │   └── gates.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── momentum_pullback.py
│   │   ├── breakout.py
│   │   ├── trend_continuation.py
│   │   ├── mean_reversion.py
│   │   ├── core_investment.py
│   │   ├── defensive_allocation.py
│   │   └── cash_deployment.py
│   └── utils/
│       ├── indicators.py
│       ├── technical_levels.py
│       ├── math_utils.py
│       ├── time_utils.py
│       └── export_utils.py
├── pages/
│   ├── 01_Mission_Control.py
│   ├── 02_Daily_Candidates.py
│   ├── 03_Screener_Search.py
│   ├── 04_Back_Book.py
│   ├── 05_Portfolio.py
│   ├── 06_Journal.py
│   └── 07_Settings.py
├── tests/
│   ├── test_chart_engine.py
│   ├── test_trade_plan_engine.py
│   ├── test_scoring.py
│   ├── test_risk_engine.py
│   ├── test_portfolio_engine.py
│   └── fixtures/
└── docs/
    ├── data_sources.md
    ├── scoring.md
    ├── strategies.md
    ├── ui_ux.md
    ├── deployment.md
    └── safety.md
```

---

# 4. Runtime Architecture

## 4.1 MVP runtime

Initial runtime:

```text
User opens Streamlit app
        |
        v
Config loader reads YAML files
        |
        v
Orchestrator runs daily pipeline
        |
        v
Data providers fetch/cache data
        |
        v
Engines compute regime, scores, chart levels, trade plans, portfolio fit
        |
        v
Recommendations are rendered in Streamlit
        |
        v
Exports/journal snapshots are saved locally
```

## 4.2 Core orchestration sequence

```text
1. Load config
2. Resolve universe
3. Load portfolio snapshot
4. Fetch market index data
5. Compute market regime
6. Fetch candidate price history
7. Compute technical indicators
8. Fetch/estimate fundamentals
9. Run strategy classification
10. Generate trade plans
11. Run risk checks
12. Run portfolio fit checks
13. Compute final Atlas scores
14. Generate AI statement / rule-based explanation
15. Sort candidates
16. Render daily view
17. Save recommendation snapshot
```

## 4.3 Provider abstraction

All data providers implement a base interface.

Provider output must include:

- provider name;
- timestamp;
- data quality state;
- source fields;
- warning list;
- raw payload optionally saved in cache.

## 4.4 Data freshness rules

Initial freshness guidelines:

| Data type | Max acceptable age | If stale |
|---|---:|---|
| Daily price data | 2 trading days | mark stale, lower confidence |
| Intraday price data | not required for MVP | not applicable |
| Fundamentals | 90 days | mark partial/stale |
| Earnings dates | 14 days | mark stale |
| Market regime | 2 trading days | show warning |
| Portfolio manual input | user-defined | show last updated |

---

# 5. Pages and UI Specification

## 5.1 Page 1 - Mission Control

Purpose: Daily high-level decision screen.

### Layout priority

1. Market traffic light;
2. Top candidates;
3. AI/rule-based summary;
4. News placeholder;
5. Portfolio development;
6. Wealth development;
7. Portfolio risk;
8. FIRE progress;
9. Calendar placeholder.

### MVP components

```text
Mission Control
├── Header
│   ├── Date
│   ├── App version
│   └── Data freshness indicator
├── Market Regime Card
│   ├── State: Risk On / Neutral / Caution / Risk Off / Pause
│   ├── Score
│   ├── Position multiplier
│   └── Drivers
├── Daily Summary Card
│   ├── One sentence verdict
│   ├── Today action list
│   └── No-trade message if applicable
├── Top Candidate Cards
│   ├── up to 5 expanded cards
│   └── link to full top 10
├── Portfolio Snapshot
│   ├── Cash
│   ├── Satellite exposure
│   ├── Tech/theme exposure placeholder
│   └── warnings
└── Export / Refresh controls
```

### Required Mission Control messages

If no candidate meets threshold:

```text
No stock met all Atlas criteria today. The best candidates are still available in the Back-Book.
```

If market is Pause:

```text
Market regime is Pause. No new satellite trades should be opened. Existing positions require review.
```

If data quality is poor:

```text
Data quality is partial. Treat recommendations as research output, not action candidates.
```

## 5.2 Page 2 - Daily Candidates

Purpose: Ranked list of up to 10 daily opportunities.

### Candidate table columns

- Rank;
- Ticker;
- Name;
- Asset type;
- Verdict;
- Strategy;
- Final Atlas Score;
- Confidence;
- Portfolio Fit;
- Entry Zone;
- Stop;
- TP1;
- TP2;
- CRV blended;
- Suggested Position EUR;
- Holding Period;
- Main Risk;
- Back-Book link.

### Candidate card fields

Each card must show:

- name/ticker;
- verdict;
- Atlas Score;
- Confidence;
- Portfolio Fit;
- Strategy;
- Entry zone;
- do-not-chase price;
- stop-loss;
- take-profit levels;
- suggested position;
- holding period;
- why now;
- key risks;
- portfolio warning;
- data quality.

## 5.3 Page 3 - Screener / Search

Purpose: Analyze a single asset or theme on demand.

### Search input types

MVP order:

1. Ticker;
2. Company or ETF name;
3. ISIN;
4. WKN;
5. Theme keyword;
6. Natural language research prompt.

ISIN/WKN support in MVP may require a mapping table. If unresolved, Atlas asks user to provide ticker/exchange.

### Single asset output

- resolved identity;
- price snapshot;
- market context;
- score breakdown;
- chart summary;
- strategy fit;
- portfolio fit;
- trade plan if valid;
- AI/rule-based statement;
- data quality;
- save to watchlist button.

## 5.4 Page 4 - Back-Book

Purpose: Explain why candidates were selected, downgraded, rejected or watched.

### Back-Book content

For each candidate:

- full score breakdown;
- raw component scores;
- market regime impact;
- chart analysis;
- fundamental summary;
- strategy rationale;
- entry/stop/TP rationale;
- CRV calculation;
- risk calculation;
- portfolio impact;
- gate rules triggered;
- downgrade reasons;
- data quality warnings;
- final verdict;
- recommendation snapshot ID.

## 5.5 Page 5 - Portfolio

Purpose: Manual portfolio context for MVP.

### MVP fields

- cash amount;
- satellite capital limit;
- current satellite deployed;
- holdings table;
- asset class allocation;
- sector/theme exposure;
- ETF overlap notes placeholder;
- warnings and rebalance hints.

### Holdings table columns

- asset_id;
- name;
- ticker;
- isin;
- wkn;
- asset_type;
- quantity;
- cost_basis;
- current_value;
- currency;
- strategy_intent;
- asset_class;
- sector;
- theme_tags;
- broker/account;
- notes.

## 5.6 Page 6 - Journal

Purpose: Store recommendations and later outcomes.

MVP can be read-only/recommendation snapshot based. Manual outcome updates can come later.

### Journal MVP fields

- recommendation_id;
- timestamp;
- ticker;
- verdict;
- strategy;
- entry zone;
- stop;
- TP1/TP2;
- score;
- confidence;
- user action: ignored / watched / entered / rejected;
- optional notes.

## 5.7 Page 7 - Settings

Purpose: User-editable config.

MVP settings:

- satellite max EUR;
- risk budget;
- max single position;
- watchlists;
- excluded sectors/themes;
- preferred themes;
- scoring weights file path;
- data provider preference;
- export path.

---

# 6. Domain Model

The MVP should use Pydantic models where practical. If Pydantic is not used initially, the same structure should be mirrored by dataclasses.

## 6.1 Enums

```python
from enum import Enum

class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    BOND = "bond"
    PRIVATE_EQUITY = "private_equity"
    STARTUP = "startup"
    OPTION = "option"
    CRYPTO = "crypto"
    OTHER = "other"

class StrategyIntent(str, Enum):
    CORE = "core"
    SWING = "swing"
    HEDGE = "hedge"
    INCOME = "income"
    DIVERSIFICATION = "diversification"
    WATCHLIST = "watchlist"
    EXPERIMENTAL = "experimental"
    CASH_DEPLOYMENT = "cash_deployment"

class MarketRegimeState(str, Enum):
    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    CAUTION = "caution"
    RISK_OFF = "risk_off"
    PAUSE = "pause"

class Verdict(str, Enum):
    STRONG_BUY = "strong_buy"
    CORE_CANDIDATE = "core_candidate"
    SATELLITE_SWING = "satellite_swing"
    WATCHLIST = "watchlist"
    HOLD = "hold"
    AVOID = "avoid"
    TOO_RISKY = "too_risky"
    GOOD_ASSET_BAD_PORTFOLIO_FIT = "good_asset_bad_portfolio_fit"
    DIVERSIFICATION_CANDIDATE = "diversification_candidate"
    CASH_PREFERRED = "cash_preferred"
    WAIT_FOR_ENTRY = "wait_for_entry"
    DO_NOT_CHASE = "do_not_chase"
    REDUCE_EXPOSURE = "reduce_exposure"
    REVIEW_REQUIRED = "review_required"

class DataQualityState(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    STALE = "stale"
    ESTIMATED = "estimated"
    MISSING = "missing"
    CONFLICTING = "conflicting"
```

## 6.2 Asset identifier

```python
class AssetIdentifier(BaseModel):
    asset_id: str
    name: str
    ticker: str | None = None
    isin: str | None = None
    wkn: str | None = None
    exchange: str | None = None
    currency: str | None = None
    asset_type: AssetType
    sector: str | None = None
    industry: str | None = None
    theme_tags: list[str] = []
```

## 6.3 Data quality

```python
class DataQuality(BaseModel):
    state: DataQualityState
    provider: str | None = None
    timestamp: datetime | None = None
    warnings: list[str] = []
    missing_fields: list[str] = []
    confidence_penalty: float = 0.0
```

## 6.4 Price snapshot

```python
class PriceSnapshot(BaseModel):
    last: float
    previous_close: float | None = None
    currency: str
    timestamp: datetime
    provider: str
    data_quality: DataQuality
```

## 6.5 OHLCV row

```python
class OhlcvRow(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
```

## 6.6 Indicator snapshot

```python
class IndicatorSnapshot(BaseModel):
    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    ema20: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    rsi14: float | None = None
    atr14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None
    relative_strength_score: float | None = None
    distance_to_ema20_pct: float | None = None
    distance_to_ema50_pct: float | None = None
    distance_to_sma200_pct: float | None = None
```

## 6.7 Chart levels

```python
class TechnicalLevel(BaseModel):
    level: float
    level_type: str
    strength: float
    rationale: list[str]

class ChartAnalysis(BaseModel):
    trend_state: str
    market_structure: str
    indicators: IndicatorSnapshot
    support_levels: list[TechnicalLevel]
    resistance_levels: list[TechnicalLevel]
    breakout_level: TechnicalLevel | None = None
    invalidation_level: TechnicalLevel | None = None
    volume_summary: str | None = None
    chart_score: float
    rationale: list[str]
    warnings: list[str] = []
```

## 6.8 Fundamental snapshot

```python
class FundamentalSnapshot(BaseModel):
    market_cap: float | None = None
    pe: float | None = None
    forward_pe: float | None = None
    peg: float | None = None
    revenue_growth_yoy: float | None = None
    eps_growth_yoy: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    roe: float | None = None
    roic: float | None = None
    debt_to_equity: float | None = None
    free_cash_flow_yield: float | None = None
    dividend_yield: float | None = None
    institutional_ownership: float | None = None
    insider_ownership: float | None = None
    analyst_revision_score: float | None = None
    data_quality: DataQuality
```

## 6.9 Market regime

```python
class MarketRegime(BaseModel):
    state: MarketRegimeState
    score: float
    drivers: dict[str, float]
    restrictions: dict[str, bool | float]
    position_multiplier: float
    min_score_required: float | None
    rationale: list[str]
    data_quality: DataQuality
```

## 6.10 Score breakdown

```python
class ScoreBreakdown(BaseModel):
    asset_score: float
    fundamental_score: float | None = None
    chart_score: float
    strategy_fit_score: float
    portfolio_fit_score: float
    risk_score: float
    market_regime_score: float
    catalyst_score: float | None = None
    final_atlas_score: float
    confidence: float
    weights_used: dict[str, float]
    gates_triggered: list[str] = []
    downgrades: list[str] = []
```

## 6.11 Trade plan

```python
class EntryZone(BaseModel):
    lower: float
    upper: float
    rationale: list[str]

class StopLoss(BaseModel):
    level: float
    type: str
    rationale: list[str]

class TakeProfitLevel(BaseModel):
    level: float | None = None
    action: str
    rationale: list[str]

class Crv(BaseModel):
    tp1: float | None = None
    tp2: float | None = None
    tp3: float | None = None
    blended: float | None = None

class SuggestedPosition(BaseModel):
    amount_eur: float
    max_amount_eur: float
    risk_eur: float
    risk_pct_satellite: float
    rationale: list[str]

class HoldingPeriod(BaseModel):
    min_days: int
    max_days: int

class Invalidation(BaseModel):
    conditions: list[str]

class TradePlan(BaseModel):
    strategy: str
    intent: StrategyIntent
    entry_zone: EntryZone | None
    do_not_chase_above: float | None
    stop_loss: StopLoss | None
    take_profit: dict[str, TakeProfitLevel]
    crv: Crv
    suggested_position: SuggestedPosition | None
    holding_period: HoldingPeriod
    invalidation: Invalidation
    data_quality: DataQuality
```

## 6.12 Recommendation

```python
class Recommendation(BaseModel):
    recommendation_id: str
    created_at: datetime
    asset: AssetIdentifier
    price: PriceSnapshot
    market_regime: MarketRegime
    chart: ChartAnalysis
    fundamentals: FundamentalSnapshot | None
    strategy: str
    intent: StrategyIntent
    verdict: Verdict
    scores: ScoreBreakdown
    trade_plan: TradePlan | None
    portfolio_fit: dict
    ai_statement: str
    key_reasons: list[str]
    key_risks: list[str]
    data_quality: DataQuality
    back_book: dict
```

---

# 7. Configuration Files

## 7.1 settings.yaml

```yaml
app:
  name: Atlas
  version: 0.1
  timezone: Europe/Vienna
  base_currency: EUR

runtime:
  cache_enabled: true
  cache_dir: data/cache
  export_dir: data/exports
  journal_dir: data/journal

providers:
  price_provider: yfinance
  fundamental_provider: yfinance
  screener_provider: manual
  ai_provider: none

ui:
  max_daily_candidates: 10
  max_frontpage_candidates: 5
  show_back_book: true
```

## 7.2 watchlists.yaml

```yaml
watchlists:
  core_quality:
    - MSFT
    - AAPL
    - GOOGL
    - AMZN
    - META
    - V
    - MA
    - COST
    - LVMUY
  ai_semis:
    - NVDA
    - AMD
    - AVGO
    - ASML
    - TSM
    - LRCX
    - AMAT
  cyber:
    - CRWD
    - PANW
    - ZS
    - FTNT
    - NET
  energy_resources:
    - XOM
    - CVX
    - COP
    - FCX
    - NEM
    - GOLD
  etfs:
    - SPY
    - QQQ
    - VOO
    - VT
    - ACWI
    - JEPQ
```

## 7.3 risk_rules.yaml

```yaml
satellite:
  max_capital_eur: 50000
  max_single_position_eur: 10000
  allow_larger_position_when_justified: true
  max_drawdown_pause_pct: 15
  target_completed_trades_per_year_min: 20
  target_completed_trades_per_year_max: 40

risk_budget:
  normal_setup_pct_of_satellite: 1.0
  high_confidence_pct_of_satellite: 1.5
  risk_off_pct_of_satellite: 0.5
  experimental_pct_of_satellite: 0.5

market_regime_multipliers:
  risk_on:
    position_multiplier: 1.0
    min_score: 80
  neutral:
    position_multiplier: 0.75
    min_score: 82
  caution:
    position_multiplier: 0.50
    min_score: 85
  risk_off:
    position_multiplier: 0.25
    min_score: 90
  pause:
    position_multiplier: 0.0
    min_score: null

crv:
  weak_tp1_below: 1.2
  downgrade_blended_below: 1.8
  attractive_blended_above: 2.5
  strong_blended_above: 3.0
```

## 7.4 scoring_weights.yaml

```yaml
default:
  market_environment: 0.15
  quality_fundamentals: 0.18
  momentum_trend: 0.17
  chart_setup_timing: 0.20
  risk_volatility_liquidity: 0.10
  portfolio_fit: 0.15
  catalyst_ai: 0.05

core_investment:
  quality_fundamentals: 0.30
  valuation: 0.15
  portfolio_fit: 0.20
  market_environment: 0.10
  chart_timing: 0.10
  risk: 0.10
  catalyst: 0.05

satellite_swing:
  chart_setup_timing: 0.30
  momentum_relative_strength: 0.25
  market_environment: 0.15
  risk_volatility_liquidity: 0.15
  portfolio_fit: 0.10
  catalyst: 0.05

diversification_hedge:
  portfolio_fit: 0.30
  market_regime: 0.20
  risk_correlation: 0.20
  chart_timing: 0.15
  liquidity: 0.10
  catalyst: 0.05

thresholds:
  strong_buy:
    min_score: 88
    min_confidence: 80
  core_candidate:
    min_score: 82
    min_confidence: 75
  satellite_swing:
    min_score: 80
    min_confidence: 75
  watchlist:
    min_score: 70
    min_confidence: 60
```

## 7.5 portfolio.yaml

```yaml
portfolio:
  last_updated: 2026-07-05
  base_currency: EUR
  cash_eur: 140000
  satellite_capital_limit_eur: 50000
  satellite_deployed_eur: 0
  holdings: []

targets:
  cash_min_eur: 40000
  cash_max_eur: 70000
  max_theme_ai_pct_total_portfolio: 25
  max_sector_technology_pct_total_portfolio: 30
  max_single_name_pct_total_portfolio: 8
  max_satellite_pct_liquid_assets: 10
```

---

# 8. Engine Interfaces

## 8.1 Orchestrator

```python
class AtlasOrchestrator:
    def run_daily_pipeline(self) -> list[Recommendation]:
        ...

    def analyze_asset(self, query: str, intent: StrategyIntent | None = None) -> Recommendation:
        ...

    def export_recommendations(self, recommendations: list[Recommendation], fmt: str) -> Path:
        ...
```

## 8.2 Universe Resolver

Responsibilities:

- resolve ticker/name/ISIN/WKN to AssetIdentifier;
- map to exchange/currency;
- attach asset type and theme tags;
- return resolution confidence.

```python
class UniverseResolver:
    def resolve(self, query: str) -> AssetIdentifier:
        ...

    def load_watchlist(self, name: str) -> list[AssetIdentifier]:
        ...

    def resolve_many(self, queries: list[str]) -> list[AssetIdentifier]:
        ...
```

MVP fallback rules:

- If query is a known ticker, resolve directly.
- If query is name, search local alias table.
- If query is ISIN/WKN and no provider supports lookup, return Review Required and ask for ticker mapping.

## 8.3 Market Engine

Responsibilities:

- determine market regime;
- compute score and drivers;
- define position multiplier;
- define minimum score threshold;
- flag risk-off or pause.

```python
class MarketEngine:
    def compute_regime(self) -> MarketRegime:
        ...
```

Initial inputs:

- SPY vs SMA200;
- QQQ vs SMA200;
- SPY 20-day trend;
- QQQ 20-day trend;
- VIX proxy when available;
- simple breadth placeholder if unavailable.

Initial scoring example:

```text
trend_score = average(index_above_sma200_score, slope_score)
volatility_score = inverse_vix_score
breadth_score = placeholder_or_provider_score
sector_score = placeholder
market_score = weighted average
```

Regime mapping:

| Market score | Regime |
|---:|---|
| >= 75 | Risk On |
| 60-74 | Neutral |
| 45-59 | Caution |
| 30-44 | Risk Off |
| < 30 | Pause |

## 8.4 Fundamental Engine

Responsibilities:

- load fundamental metrics;
- compute quality score;
- compute valuation score when possible;
- mark missing values clearly.

```python
class FundamentalEngine:
    def analyze(self, asset: AssetIdentifier) -> FundamentalSnapshot:
        ...

    def score(self, fundamentals: FundamentalSnapshot, asset_type: AssetType) -> float:
        ...
```

Initial fundamental score inputs:

- market cap;
- revenue growth;
- EPS growth;
- margins;
- ROE/ROIC;
- debt-to-equity;
- free cash flow yield;
- institutional/insider ownership if available;
- dividend yield only when relevant.

MVP may use partial fundamentals and reduce confidence.

## 8.5 Chart Engine

Responsibilities:

- compute indicators;
- identify trend;
- identify support and resistance;
- identify market structure;
- produce chart score;
- produce technical levels for Trade Plan Engine.

```python
class ChartEngine:
    def analyze(self, asset: AssetIdentifier, price_history: list[OhlcvRow]) -> ChartAnalysis:
        ...
```

Initial indicators:

- SMA20;
- SMA50;
- SMA200;
- EMA20;
- EMA50;
- RSI14;
- ATR14;
- 20-day high/low;
- 50-day high/low;
- 200-day high/low;
- volume average;
- distance to moving averages.

Initial chart scoring:

| Factor | Weight |
|---|---:|
| Trend above SMA200 | 20 |
| Price above SMA50 | 15 |
| EMA20/EMA50 structure | 15 |
| RSI healthy range | 10 |
| Pullback quality | 15 |
| Support confluence | 15 |
| Volume confirmation | 10 |

Chart score should be 0-100.

## 8.6 Strategy Engine

Responsibilities:

- classify setup;
- assign intent;
- decide strategy fit;
- run strategy-specific gates.

```python
class StrategyEngine:
    def classify(self, asset: AssetIdentifier, chart: ChartAnalysis, fundamentals: FundamentalSnapshot | None, market: MarketRegime) -> str:
        ...

    def score_fit(self, strategy: str, chart: ChartAnalysis, fundamentals: FundamentalSnapshot | None) -> float:
        ...
```

Initial strategies:

- Momentum Pullback;
- Breakout;
- Trend Continuation;
- Mean Reversion;
- Core Investment;
- Defensive Allocation;
- Event Driven placeholder;
- Cash Deployment;
- ETF Core Allocation.

## 8.7 Trade Plan Engine

Responsibilities:

- generate entry zone;
- generate do-not-chase price;
- generate stop-loss;
- generate TP1/TP2/TP3;
- calculate CRV;
- calculate position size;
- define invalidation;
- define holding period.

```python
class TradePlanEngine:
    def generate(self, asset: AssetIdentifier, price: PriceSnapshot, chart: ChartAnalysis, strategy: str, risk_context: dict) -> TradePlan:
        ...
```

Trade Plan Engine may return incomplete plan. Incomplete plan triggers downgrade to Watchlist or Review Required.

## 8.8 Risk Engine

Responsibilities:

- apply market regime multipliers;
- enforce satellite risk rules;
- reject low-liquidity setups;
- downgrade poor CRV;
- pause when drawdown threshold reached.

```python
class RiskEngine:
    def evaluate(self, recommendation: Recommendation, portfolio: dict, risk_rules: dict) -> dict:
        ...

    def position_size(self, trade_plan: TradePlan, confidence: float, market: MarketRegime, portfolio_fit_score: float) -> SuggestedPosition:
        ...
```

## 8.9 Portfolio Engine

Responsibilities:

- compute current exposure;
- compute post-trade exposure;
- generate Portfolio Fit score;
- warn about concentration;
- suggest possible correction, not forced action.

```python
class PortfolioEngine:
    def snapshot(self) -> dict:
        ...

    def fit(self, asset: AssetIdentifier, proposed_amount_eur: float, intent: StrategyIntent) -> dict:
        ...
```

Portfolio Engine can output:

- improves;
- neutral;
- worsens;
- concentration risk;
- diversification candidate.

## 8.10 AI Narrative Engine

Responsibilities:

- generate concise explanation;
- include only structured facts from engines;
- avoid unsupported claims;
- separate facts, interpretation and open questions.

```python
class AINarrativeEngine:
    def summarize_daily(self, recommendations: list[Recommendation], market: MarketRegime, portfolio: dict) -> str:
        ...

    def explain_candidate(self, recommendation: Recommendation) -> str:
        ...
```

MVP can use deterministic templates instead of live AI.

## 8.11 Journal Engine

Responsibilities:

- store recommendation snapshots;
- allow user action tagging;
- later track outcomes.

```python
class JournalEngine:
    def save_recommendation(self, recommendation: Recommendation) -> str:
        ...

    def update_user_action(self, recommendation_id: str, action: str, notes: str | None = None) -> None:
        ...
```

---

# 9. Scoring Specification

## 9.1 Score scale

All component scores use 0-100.

Interpretation:

| Score | Meaning |
|---:|---|
| 90-100 | Exceptional |
| 80-89 | Strong |
| 70-79 | Watchlist / acceptable |
| 60-69 | Weak |
| <60 | Not attractive |

## 9.2 Default formula

```text
raw_score = sum(component_score * component_weight)
```

Then apply gates and downgrades:

```text
final_score = raw_score
final_score -= data_quality_penalty
final_score -= gate_penalties
final_score = clamp(final_score, 0, 100)
```

Position size uses multipliers, not score directly.

## 9.3 Decision score vs asset score

Asset Score evaluates the asset.

Decision Score evaluates whether this asset is a good decision today for Mario.

```text
decision_score = weighted_score_after_strategy + portfolio_fit_adjustment + risk_adjustment
```

A high-quality asset can become a weak Atlas decision if:

- portfolio concentration is already high;
- market regime is Risk Off;
- no logical stop exists;
- CRV is poor;
- data quality is low;
- earnings event risk is too high;
- entry has already been missed.

## 9.4 Confidence score

Confidence is not the same as attractiveness.

Inputs:

- data completeness;
- data freshness;
- agreement across engines;
- chart clarity;
- fundamental data quality;
- CRV clarity;
- portfolio data quality.

Initial formula:

```text
confidence = 100
confidence -= missing_data_penalty
confidence -= stale_data_penalty
confidence -= conflicting_signal_penalty
confidence -= unclear_chart_penalty
confidence = clamp(confidence, 0, 100)
```

## 9.5 Gate rules

Hard gates:

- missing price data -> Review Required;
- no stop-loss possible -> Watchlist only;
- blended CRV below 1.8 -> downgrade;
- market regime Pause -> no new satellite trades;
- satellite drawdown below -15% -> no new satellite trades;
- liquidity too low -> Avoid for satellite;
- data quality Missing -> no formal recommendation.

Soft gates:

- Risk Off -> smaller position, higher minimum score;
- high concentration -> downgrade or swing only;
- earnings soon -> reduce position or wait;
- price above do-not-chase -> Wait for Entry or Do Not Chase;
- excessive gap up -> Wait for Entry.

## 9.6 Verdict selection logic

Pseudocode:

```python
if hard_gate_missing_data:
    verdict = REVIEW_REQUIRED
elif market.state == PAUSE and intent == SWING:
    verdict = WATCHLIST
elif final_score >= 88 and confidence >= 80 and portfolio_fit >= 80:
    verdict = STRONG_BUY
elif intent == CORE and final_score >= 82 and confidence >= 75:
    verdict = CORE_CANDIDATE
elif intent == SWING and final_score >= 80 and confidence >= 75 and trade_plan_complete:
    verdict = SATELLITE_SWING
elif final_score >= 70:
    verdict = WATCHLIST
else:
    verdict = AVOID
```

Portfolio concentration can override:

```python
if asset_score >= 85 and portfolio_fit < 65:
    verdict = GOOD_ASSET_BAD_PORTFOLIO_FIT
```

---

# 10. Strategy Specification

## 10.1 Momentum Pullback

Use when:

- price is above SMA200;
- price is above or near SMA50;
- trend is intact;
- pullback to EMA20/EMA50/support;
- RSI is not extremely overbought;
- relative strength remains high.

Entry:

- near EMA20/EMA50/support confluence;
- preferably after stabilization candle;
- entry zone width can be 0.5 ATR to 1 ATR.

Stop:

- below recent swing low or support cluster;
- at least normal noise distance using ATR;
- not arbitrary fixed percentage.

TP:

- TP1 at prior high or 1R-1.5R;
- TP2 at measured move or next resistance;
- TP3 trailing stop if trend continues.

Holding period:

- 2-8 weeks.

## 10.2 Breakout

Use when:

- price clears a clear resistance or base;
- volume expansion occurs;
- market regime is not hostile;
- relative strength improves.

Entry:

- breakout close;
- or retest of breakout level;
- do not chase if price is extended beyond ATR threshold.

Stop:

- below breakout level or failed breakout zone.

TP:

- measured move from base;
- next resistance;
- trailing stop after TP1.

Holding period:

- 1-6 weeks.

## 10.3 Trend Continuation

Use when:

- trend is very strong;
- pullbacks are shallow;
- price rides EMA20;
- sector leadership is strong.

Entry:

- minor consolidation;
- low-volatility pause;
- bounce from EMA20.

Risk:

- avoid if already far above EMA20/EMA50.

## 10.4 Mean Reversion

Use sparingly.

Use when:

- quality asset is oversold;
- price reaches major support;
- RSI is depressed but not structurally broken;
- market regime allows selective trades.

Entry:

- near support;
- after reversal signal.

Stop:

- below support/invalidation.

This strategy should use smaller position sizes.

## 10.5 Core Investment

Use when:

- high-quality asset;
- strong business model;
- acceptable valuation;
- good portfolio fit;
- long-term thesis is clear.

Entry:

- does not require perfect timing;
- can use staged entry;
- chart timing should avoid obvious overextension.

Stop:

- no automatic tight stop for core;
- use thesis invalidation, allocation limits, or long-term review triggers.

## 10.6 ETF Core Allocation

Use when:

- cash is above target;
- broad diversification improves FIRE probability;
- single-name concentration is high;
- market is acceptable for staged deployment.

Entry:

- scheduled or staged;
- less dependent on short-term chart;
- can use market regime to pace deployment.

## 10.7 Defensive Allocation

Use for:

- gold;
- cash;
- defensive ETFs;
- hedges.

Decision factor:

- portfolio resilience;
- not standalone upside.

---

# 11. Trade Plan Specification

## 11.1 Mandatory output for formal candidate

A formal candidate must include:

- strategy;
- intent;
- verdict;
- entry zone;
- do-not-chase price;
- stop-loss;
- TP1;
- TP2;
- TP3 or trailing plan;
- CRV;
- position size;
- holding period;
- invalidation conditions;
- key reasons;
- key risks;
- portfolio impact;
- confidence;
- data quality.

If any of entry, stop, or CRV is missing, candidate cannot be Strong Buy or Satellite Swing.

## 11.2 Entry zone algorithm v0.1

Inputs:

- last price;
- EMA20;
- EMA50;
- SMA200;
- support levels;
- resistance levels;
- ATR14;
- strategy;
- recent swing lows/highs.

For Momentum Pullback:

```text
anchor_candidates = [EMA20, EMA50, nearest_support, fib_retracement_placeholder]
entry_mid = strongest confluence near current price
entry_lower = entry_mid - 0.25 * ATR14
entry_upper = entry_mid + 0.25 * ATR14
```

If no confluence exists:

```text
entry_zone = null
verdict downgrade = Watchlist
reason = no technical entry confluence
```

For Breakout:

```text
entry_lower = breakout_level
entry_upper = breakout_level + 0.50 * ATR14
```

For Core ETF:

```text
entry_zone = staged entry, not single tactical level
```

## 11.3 Do-not-chase algorithm v0.1

For swing trades:

```text
do_not_chase = min(nearest_resistance * 0.985, entry_upper + 1.0 * ATR14)
```

If price is above do_not_chase:

- verdict becomes Wait for Entry or Do Not Chase;
- candidate may remain in Back-Book.

## 11.4 Stop-loss algorithm v0.1

Candidate stop anchors:

- swing low;
- nearest support;
- EMA50;
- ATR stop;
- breakout failure level.

For Momentum Pullback:

```text
stop = min(recent_swing_low, nearest_support) - 0.25 * ATR14
```

For Breakout:

```text
stop = breakout_level - 0.50 * ATR14
```

For Mean Reversion:

```text
stop = major_support - 0.50 * ATR14
```

Validation:

```text
stop_distance_pct = (entry_mid - stop) / entry_mid
```

If stop_distance_pct is too small, normal noise may stop out position. If too large, position size becomes too small or CRV becomes weak.

## 11.5 Take-profit algorithm v0.1

TP candidates:

- prior high;
- nearest resistance;
- measured move;
- 1R/2R/3R;
- ATR extension;
- trailing stop.

Initial default:

```text
risk_per_share = entry_mid - stop
TP1 = max(nearest_resistance, entry_mid + 1.25 * risk_per_share)
TP2 = entry_mid + 2.0 * risk_per_share
TP3 = trailing stop after TP2 or entry_mid + 3.0 * risk_per_share
```

Actions:

- TP1: sell 30-50%, move stop to breakeven if appropriate;
- TP2: sell another 25-50%;
- TP3: trail remainder.

## 11.6 CRV calculation

```text
CRV_TP1 = (TP1 - entry_mid) / (entry_mid - stop)
CRV_TP2 = (TP2 - entry_mid) / (entry_mid - stop)
CRV_TP3 = (TP3 - entry_mid) / (entry_mid - stop)
blended_CRV = weighted average of TP1/TP2/TP3 using planned exit weights
```

Default exit weights:

```yaml
TP1: 0.40
TP2: 0.40
TP3: 0.20
```

## 11.7 Position sizing algorithm v0.1

Inputs:

- satellite capital max EUR;
- risk budget pct;
- market multiplier;
- confidence multiplier;
- portfolio fit multiplier;
- stop distance pct;
- max single position cap.

Risk budget:

```text
base_risk_eur = satellite_capital * risk_budget_pct
```

Multipliers:

```text
adjusted_risk_eur = base_risk_eur * market_multiplier * confidence_multiplier * portfolio_fit_multiplier
```

Position:

```text
position_eur = adjusted_risk_eur / stop_distance_pct
position_eur = min(position_eur, max_single_position_eur)
```

Confidence multiplier v0.1:

| Confidence | Multiplier |
|---:|---:|
| >= 90 | 1.20 |
| 80-89 | 1.00 |
| 70-79 | 0.75 |
| <70 | 0.50 |

Portfolio fit multiplier v0.1:

| Portfolio Fit | Multiplier |
|---:|---:|
| >= 85 | 1.00 |
| 70-84 | 0.75 |
| 55-69 | 0.50 |
| <55 | 0.25 |

## 11.8 Holding period defaults

| Strategy | Min days | Max days |
|---|---:|---:|
| Momentum Pullback | 10 | 40 |
| Breakout | 5 | 30 |
| Trend Continuation | 10 | 60 |
| Mean Reversion | 3 | 20 |
| Core Investment | 365 | 3650 |
| ETF Core Allocation | 365 | 3650 |
| Defensive Allocation | 30 | 365 |

---

# 12. Portfolio Fit Specification

## 12.1 Purpose

Portfolio Fit determines whether a good asset is a good decision for Mario today.

## 12.2 Inputs

- current holdings;
- cash;
- satellite deployed capital;
- asset class allocation;
- sector exposure;
- theme exposure;
- single-name exposure;
- proposed trade amount;
- asset correlation placeholder;
- intent;
- FIRE relevance.

## 12.3 Output fields

```yaml
portfolio_fit:
  score: 0-100
  verdict: improves | neutral | worsens | concentration_risk | diversification_candidate
  warnings: []
  suggestions: []
  current_exposure: {}
  post_trade_exposure: {}
```

## 12.4 Initial scoring

| Dimension | Weight |
|---|---:|
| Asset class balance | 20 |
| Sector balance | 20 |
| Theme balance | 20 |
| Single-name concentration | 15 |
| Liquidity | 10 |
| FIRE relevance | 10 |
| Tax/friction placeholder | 5 |

## 12.5 Downgrade examples

Nvidia:

- high asset score;
- high AI/Tech exposure in portfolio;
- downgrade to Satellite Swing only or smaller size.

Visa:

- strong payment theme;
- lower AI correlation;
- potentially better portfolio fit.

World ETF:

- may have lower standalone excitement;
- high portfolio fit if cash is high or diversification is needed.

---

# 13. Data Providers

## 13.1 MVP provider choices

Initial free/low-friction providers:

- yfinance for price history and partial fundamentals;
- manual CSV/YAML for portfolio;
- manual watchlist;
- optional Finviz manual export/import later;
- optional OpenAI/Claude for AI statements later.

## 13.2 Provider interface

```python
class PriceProvider(Protocol):
    def get_price_history(self, asset: AssetIdentifier, period: str = "1y") -> list[OhlcvRow]:
        ...

    def get_price_snapshot(self, asset: AssetIdentifier) -> PriceSnapshot:
        ...

class FundamentalProvider(Protocol):
    def get_fundamentals(self, asset: AssetIdentifier) -> FundamentalSnapshot:
        ...

class ScreenerProvider(Protocol):
    def get_universe(self, filters: dict) -> list[AssetIdentifier]:
        ...
```

## 13.3 Data quality handling

If provider returns incomplete data:

- compute what is possible;
- mark missing fields;
- reduce confidence;
- never invent values;
- show warning in UI.

---

# 14. AI Narrative Specification

## 14.1 MVP mode

MVP may use deterministic templates instead of live AI.

Template example:

```text
{ticker} is classified as {strategy} with a final Atlas Score of {score}. The setup is supported by {top_chart_reason} and {market_reason}. Portfolio fit is {portfolio_fit} because {portfolio_reason}. Entry zone is {entry_lower}-{entry_upper}, stop is {stop}, and TP1/TP2 are {tp1}/{tp2}. Main risk: {main_risk}.
```

## 14.2 AI guardrails

AI must:

- not invent price levels;
- not invent fundamentals;
- not state certainty;
- cite internal engine outputs where possible;
- separate fact from interpretation;
- disclose data gaps;
- keep recommendation as decision support only.

## 14.3 AI statement structure

```text
1. Verdict sentence
2. Why now
3. Technical setup
4. Portfolio fit
5. Risk and invalidation
6. What to watch next
```

---

# 15. Journal and Learning Specification

## 15.1 Recommendation snapshot

Each recommendation must be stored as JSON.

Filename pattern:

```text
data/journal/recommendations/YYYY-MM-DD/{recommendation_id}.json
```

## 15.2 User action states

- ignored;
- watched;
- entered;
- rejected;
- paper_trade;
- closed;
- reviewed.

## 15.3 Outcome tracking later

Fields to add in Sprint 5:

- actual entry;
- actual exit;
- max favorable excursion;
- max adverse excursion;
- TP1 hit date;
- stop hit date;
- result percent;
- result EUR;
- notes;
- lesson.

## 15.4 Learning metrics later

- hit rate;
- average gain;
- average loss;
- profit factor;
- expectancy;
- strategy performance;
- regime-specific performance;
- chart-pattern performance;
- average CRV vs realized CRV.

---

# 16. MVP Tickets

## Ticket 0.1 - Repository Bootstrap

Goal: Create project structure and install dependencies.

Deliverables:

- repository folders;
- requirements.txt;
- README.md;
- config files;
- sample watchlist;
- sample portfolio;
- Streamlit hello page.

Acceptance criteria:

- `streamlit run app.py` starts;
- Settings load from YAML;
- no secrets in repo.

## Ticket 0.2 - Domain Models

Goal: Implement core models and enums.

Deliverables:

- `atlas_core/models.py`;
- `atlas_core/enums.py`;
- unit tests for model creation.

Acceptance criteria:

- Recommendation object can be serialized to JSON;
- DataQuality object appears in all provider outputs.

## Ticket 0.3 - Provider Layer MVP

Goal: Fetch price history for tickers.

Deliverables:

- base provider protocol;
- yfinance provider;
- cache layer;
- error handling.

Acceptance criteria:

- price history loads for MSFT, NVDA, V, QQQ;
- stale/missing data flags are shown.

## Ticket 1.1 - Market Engine

Goal: Compute basic market regime.

Deliverables:

- SPY/QQQ trend check;
- SMA200 logic;
- regime score;
- position multiplier.

Acceptance criteria:

- returns Risk On/Neutral/Caution/Risk Off/Pause;
- output includes rationale;
- UI shows traffic light.

## Ticket 1.2 - Chart Engine

Goal: Compute technical indicators and chart score.

Deliverables:

- SMA/EMA;
- RSI14;
- ATR14;
- support/resistance approximations;
- chart score;
- rationale.

Acceptance criteria:

- returns ChartAnalysis for each watchlist ticker;
- no crash on missing volume;
- chart score is 0-100.

## Ticket 1.3 - Strategy Engine

Goal: Classify basic strategies.

Deliverables:

- Momentum Pullback;
- Breakout;
- Trend Continuation;
- Watchlist fallback.

Acceptance criteria:

- every candidate gets strategy or Watchlist;
- rationale explains classification.

## Ticket 1.4 - Trade Plan Engine

Goal: Generate entry/stop/TP/CRV.

Deliverables:

- entry zone algorithm;
- stop algorithm;
- TP1/TP2;
- CRV;
- do-not-chase;
- invalidation.

Acceptance criteria:

- no Satellite Swing without stop;
- no Strong Buy without CRV;
- incomplete plans are downgraded.

## Ticket 1.5 - Atlas Score

Goal: Compute final score and verdict.

Deliverables:

- weight config;
- strategy-specific weights;
- gate rules;
- confidence score.

Acceptance criteria:

- each candidate has score breakdown;
- gates are visible in Back-Book.

## Ticket 1.6 - Mission Control UI

Goal: Display daily status.

Deliverables:

- market card;
- top 5 candidates;
- daily summary;
- portfolio warning placeholder;
- export button.

Acceptance criteria:

- page is usable on desktop and iPad;
- no dense table on first screen.

## Ticket 1.7 - Daily Candidates UI

Goal: Show top 10 candidates.

Deliverables:

- ranked table;
- candidate cards;
- score fields;
- trade plan fields;
- data quality labels.

Acceptance criteria:

- user can sort/filter;
- user can export CSV.

## Ticket 2.1 - Search MVP

Goal: Analyze single ticker/name.

Deliverables:

- search input;
- resolver;
- single asset analysis page;
- save to watchlist.

Acceptance criteria:

- MSFT, NVDA, V, QQQ work;
- unresolved ISIN/WKN produces clear message.

## Ticket 2.2 - Back-Book MVP

Goal: Explain candidate decisions.

Deliverables:

- detail page;
- score breakdown;
- gates;
- rationale;
- raw internal data snapshot.

Acceptance criteria:

- every top candidate links to Back-Book;
- reasons and risks are visible.

## Ticket 3.1 - Portfolio MVP

Goal: Manual portfolio context.

Deliverables:

- load portfolio.yaml;
- holdings table;
- exposure calculations;
- portfolio fit score.

Acceptance criteria:

- proposed trade produces post-trade exposure;
- concentration warnings appear.

## Ticket 4.1 - AI Statement Placeholder

Goal: Generate structured narrative from engine outputs.

Deliverables:

- deterministic explanation template;
- optional AI provider abstraction.

Acceptance criteria:

- no unsupported claims;
- output includes verdict, why now, setup, portfolio fit, risk.

---

# 17. Testing Plan

## 17.1 Unit tests

Minimum unit tests:

- indicator calculations;
- market regime mapping;
- CRV calculation;
- position sizing;
- score weighting;
- gate rules;
- data quality penalties.

## 17.2 Fixture tickers

Use stable test tickers:

- MSFT;
- NVDA;
- V;
- QQQ;
- SPY;
- GOLD;
- JEPQ.

## 17.3 Recommendation quality tests

Test that:

- recommendation has ID;
- recommendation has data quality;
- Satellite Swing has entry/stop/TP;
- CRV below threshold downgrades;
- Pause regime blocks new satellite trades;
- missing price data returns Review Required.

## 17.4 Manual QA checklist

Before release:

- run app locally;
- load default watchlist;
- check candidate count;
- inspect one Back-Book;
- export CSV;
- edit config;
- verify no secrets committed;
- verify no automated order functionality exists.

---

# 18. Deployment Plan

## 18.1 Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 18.2 Streamlit Cloud

Requirements:

- GitHub repository;
- requirements.txt;
- app.py entrypoint;
- no private API keys in repo;
- secrets managed through Streamlit secrets.

## 18.3 Render/Railway later

Use when:

- scheduled jobs are required;
- background tasks are needed;
- database becomes persistent;
- API backend is separated from frontend.

## 18.4 Netlify later

Use only after React/Next.js frontend exists. Streamlit is not a native Netlify workload.

---

# 19. Security and Safety

## 19.1 No automated trading

MVP must not connect to broker APIs for order placement.

## 19.2 Secrets

- no API keys in code;
- use `.env` locally;
- use platform secrets in hosted environments;
- provide `.env.example` only.

## 19.3 External code

Do not execute unknown scripts from internet sources without inspection.

## 19.4 Financial framing

Atlas output is decision support. It is not a guarantee and not automated financial advice.

## 19.5 Auditability

Every recommendation should be reconstructable from stored inputs and config version.

---

# 20. Claude Build Prompt v0.1

Use this prompt when handing Atlas to Claude Code or another coding agent.

```text
You are assisting with the Atlas project, a personal Wealth Operating System for Mario.

Read ATLAS_BIBLE.md and ATLAS_SPEC.md first. The Bible defines durable philosophy. The Spec defines implementation requirements.

Your task is to implement the next ticket only. Do not add auto-trading. Do not add broker order execution. Do not store secrets in code. Keep business logic inside atlas_core engines, not Streamlit pages.

Implementation standards:
- Python first.
- Streamlit MVP.
- Use structured models.
- Every recommendation must include data quality.
- No Satellite Swing recommendation without entry, stop-loss, TP and CRV.
- Explain downgrades and gate rules.
- Add tests for new logic.
- Keep code modular.

Before coding:
1. Restate the ticket.
2. Identify files to modify.
3. Identify tests to add.
4. Ask if any ambiguity blocks implementation.

After coding:
1. Summarize changes.
2. Provide run instructions.
3. List tests.
4. List known limitations.
```

---

# 21. MVP Definition of Done

A feature is done only if:

- it works with default config;
- it handles missing data;
- it exposes data quality;
- it has at least basic tests;
- it does not mix UI and business logic;
- it does not create auto-trading paths;
- it is documented in README or docs;
- it can be reproduced from config and cached data.

A recommendation is valid only if:

- asset is resolved;
- data quality is not Missing;
- market regime is known;
- score breakdown exists;
- strategy is assigned;
- verdict is assigned;
- key reasons exist;
- key risks exist;
- trade plan exists for formal swing candidates;
- back-book record exists.

---

# 22. Open Technical Questions

## 22.1 Data source questions

- Which provider should resolve ISIN/WKN reliably?
- Should Finviz Elite be integrated through export/import first?
- Is TradingView data accessible in a stable and compliant way?
- Should market breadth be sourced from a paid provider?

## 22.2 UI questions

- Is Streamlit theming sufficient for Atlas v0.1?
- Should mobile optimization be done in Streamlit first or later in React?
- How dense should the Back-Book be on iPad?

## 22.3 Portfolio questions

- How exact should ETF overlap analysis be in MVP?
- Should portfolio be entered manually or imported from broker exports?
- How often should portfolio values be refreshed?

## 22.4 AI questions

- Should MVP use no AI, template AI, or API-based AI?
- Which parts require strict deterministic logic before AI summary?
- Should AI statements be stored with each recommendation snapshot?

## 22.5 Scoring questions

- Should weights be optimized through backtests later?
- Should sector-specific weights exist?
- Should ETF scoring be completely separate from stock scoring?

---

# 23. Immediate Next Steps

## Step 1 - Freeze documentation baseline

- Save ATLAS_BIBLE_v0.2_PRO.md as `ATLAS_BIBLE.md`.
- Save this file as `ATLAS_SPEC.md`.
- Add both to repository root.

## Step 2 - Start Sprint 0

Implement:

- repo structure;
- config files;
- domain models;
- provider stubs;
- Streamlit shell.

## Step 3 - Start Sprint 1

Implement in order:

1. Market Engine;
2. Chart Engine;
3. Strategy Engine;
4. Trade Plan Engine;
5. Atlas Score;
6. Mission Control UI;
7. Daily Candidates UI.

## Step 4 - Review output with Mario

Review first daily candidate output manually.

Focus on:

- are recommendations useful?
- are entries plausible?
- are stops technically meaningful?
- are CRV and position size sane?
- is Portfolio Fit doing what Mario expects?

---

# 24. Changelog

## v0.1 - 2026-07-05

Initial implementation specification created from ATLAS_BIBLE_v0.2_PRO.

Includes:

- repository structure;
- runtime architecture;
- page specs;
- domain models;
- config files;
- engine interfaces;
- scoring rules;
- strategy specs;
- trade plan algorithms;
- portfolio fit logic;
- data provider abstraction;
- AI narrative guardrails;
- journal plan;
- MVP tickets;
- testing plan;
- deployment plan;
- Claude build prompt;
- definition of done.
