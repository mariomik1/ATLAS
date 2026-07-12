# ATLAS BIBLE

**Version:** 0.2 Pro Review  
**Status:** Foundation + Product/Architecture Review  
**Owner:** Mario Mikikits  
**Project:** Atlas - Personal Wealth Operating System  
**Last updated:** 2026-07-04  
**Classification:** Personal / Internal  
**Source:** Based on ATLAS_BIBLE_v0.1 and subsequent Pro-Mode review  

---

## 0. Document Purpose

This document is the current **single source of truth** for Atlas.

Atlas began as an idea for a stock screener and has evolved into a personal **Wealth Operating System**: a decision cockpit for financial freedom, portfolio control, market opportunities, risk management, and structured learning.

Version 0.2 upgrades the v0.1 foundation into a more professional product and architecture document. It does not replace future specifications. Instead, it defines the durable principles, product intent, decision logic, system architecture, risk rules, and development direction.

### 0.1 How this document should be used

Use this Bible whenever:

- a new chat, agent, developer, or coding tool joins the project;
- a major product decision is unclear;
- scoring or strategy rules are changed;
- a feature is proposed and needs to be checked against the Atlas mission;
- Claude, ChatGPT, GitHub agents, or future Skills need project context;
- Atlas needs to stay coherent across months or years of development.

### 0.2 What belongs here vs. in specs

The Atlas Bible contains the **why** and the durable architecture:

- mission;
- principles;
- investment philosophy;
- user profile;
- system architecture;
- high-level modules;
- risk and governance rules;
- strategic roadmap.

The Atlas Specs should contain the **how**:

- exact UI layouts;
- API schemas;
- database tables;
- formulas;
- implementation tickets;
- sprint details;
- prompts;
- code-level rules;
- provider-specific integration details.

Recommended project documentation structure:

```text
Atlas/
├── README.md
├── ATLAS_BIBLE.md
├── ATLAS_SPEC.md
├── CHANGELOG.md
├── docs/
│   ├── architecture.md
│   ├── scoring.md
│   ├── strategies.md
│   ├── ui_ux.md
│   ├── data_sources.md
│   └── governance.md
├── specs/
│   ├── sprint_1_investment_engine.md
│   ├── sprint_2_portfolio_engine.md
│   └── sprint_3_ai_backbook.md
├── prompts/
│   ├── claude_build_prompt.md
│   ├── chatgpt_review_prompt.md
│   └── daily_ai_statement.md
└── data/
    ├── portfolio_schema.json
    ├── risk_rules.json
    └── strategy_config.yaml
```

---

# 1. Executive Summary

## 1.1 What Atlas is

Atlas is Mario's personal **Wealth Operating System**.

It is not merely a screener. It is a structured decision platform designed to answer one central question:

> **Which decision brings Mario's total wealth closest to financial freedom today while avoiding severe, hard-to-recover losses?**

Atlas combines:

- market regime assessment;
- stock and ETF screening;
- chart-based trade planning;
- portfolio steering;
- risk management;
- FIRE progress tracking;
- cash deployment logic;
- real estate opportunity analysis;
- AI-supported research;
- trade journaling;
- learning from outcomes.

## 1.2 What Atlas optimizes

Atlas does **not** primarily optimize for:

- number of trades;
- maximum short-term return;
- excitement;
- daily activity;
- beating MSCI World every single year.

Atlas optimizes for:

1. **wealth growth**;
2. **earlier FIRE goal achievement**;
3. **risk-adjusted decision quality**;
4. **avoidance of major portfolio damage**;
5. **repeatable, explainable decision processes**.

## 1.3 North Star

The aspirational North Star is:

> **Through Atlas, Mario achieves in 5 years the financial goals originally planned for 15 years, becoming financially independent 10 years earlier.**

This is an ambition, not a promise. Atlas must never imply certainty. It should improve discipline, timing, information quality, risk control, and capital allocation.

## 1.4 Core shift from v0.1 to v0.2

Version 0.1 described the concept. Version 0.2 professionalizes it.

Main upgrades:

- clearer engine boundaries;
- clearer risk governance;
- stronger separation between asset score and decision score;
- formal trade-plan requirements;
- chart-technical decision framework;
- data-contract thinking;
- development governance;
- backtesting and learning requirements;
- acceptance criteria for MVP work;
- Atlas/Claude/ChatGPT multi-agent workflow;
- first structure for an eventual Atlas Skill.

---

# 2. Atlas Principles

These principles are the durable operating rules of Atlas. They should not be changed casually.

## Principle 1 - FIRE First

Atlas exists to support Mario's path to financial freedom. Every recommendation must be interpreted through the lens of goal achievement.

A trade can be profitable and still be a bad Atlas decision if it increases concentration, volatility, or behavioral risk in a way that harms long-term independence.

## Principle 2 - Wealth Before Trade Performance

Atlas measures success at the wealth-system level, not at the single-trade level.

A trade that makes +8% but creates bad habits, increases concentration, or violates risk discipline is not necessarily successful.

A decision to do nothing can be a successful Atlas decision.

## Principle 3 - Atlas Evaluates Decisions, Not Just Assets

The key question is not:

> Is Nvidia a good company?

The key question is:

> Is Nvidia a good decision for Mario today, given his portfolio, risk, timeframe, strategy intent, market regime, and FIRE objective?

This is the central differentiation of Atlas.

## Principle 4 - Every Position Needs a Purpose

Every position must have a declared intent before it can be evaluated.

Allowed intents:

- Core holding;
- Satellite swing trade;
- Long-term megatrend;
- Income/cashflow;
- Diversification;
- Hedge;
- Opportunistic trade;
- Real estate allocation;
- Cash reserve;
- Watchlist only;
- Experimental strategy.

The same asset can have different verdicts depending on intent. Example:

- Nvidia as long-term core: possibly downgraded due to Tech/AI concentration.
- Nvidia as 3-4 week swing: possibly acceptable with small size and clear stop.
- Nvidia as hedge: not suitable.

## Principle 5 - Risk Comes Before Excitement

Mario selected the uncertainty bias:

> Prefer missing a chance over entering a bad trade.

Atlas should not force trades. If no setup is strong enough, Atlas should say:

> **Heute wurde keine Aktie gefunden, die alle Qualitätskriterien erfüllt. Die besten Kandidaten werden dennoch im Back-Book angezeigt.**

## Principle 6 - Portfolio Fit Matters as Much as Asset Quality

A strong asset can be a weak portfolio decision.

Atlas must always distinguish:

- **Asset Score**: how attractive the asset is on its own;
- **Portfolio Fit Score**: whether it improves Mario's total portfolio;
- **Decision Score**: whether the action is suitable now;
- **Confidence**: how reliable the setup is based on data quality and confluence.

## Principle 7 - Every Recommendation Must Include a Complete Plan

Atlas must never output a naked buy idea.

Every daily candidate requires:

- strategy;
- thesis;
- entry zone;
- do-not-chase price;
- stop-loss;
- TP1, TP2, TP3 or trailing stop;
- chance/risk ratio;
- suggested position size;
- time horizon;
- invalidation conditions;
- portfolio impact;
- key risks;
- AI statement;
- back-book link.

If these cannot be calculated, the asset cannot be a formal recommendation. It can only be watchlist/research.

## Principle 8 - Chart Levels Must Be Technically Meaningful

Entry, stop-loss, and take-profit must be derived from market structure, not arbitrary percentages.

Allowed anchors include:

- support and resistance;
- swing highs/lows;
- EMA20/EMA50/SMA200;
- VWAP;
- ATR;
- Fibonacci levels;
- gap zones;
- consolidation ranges;
- volume profile;
- breakout/retest zones;
- relative strength;
- volatility compression;
- trend channels.

Fixed percentages may only be fallback logic.

## Principle 9 - Atlas Must Be Explainable

Each recommendation has two layers:

1. **Daily layer**: short, clear, actionable.
2. **Back-book layer**: full analysis with data, scores, assumptions, alternatives, risks and why the recommendation was accepted or rejected.

The user must never feel forced to trust a black box.

## Principle 10 - Atlas May Disagree

Atlas is allowed to warn clearly.

Mario selected correction mode **B**:

- Atlas should not hard-block decisions;
- Atlas should clearly warn;
- Atlas should suggest safer alternatives.

Example:

> Nvidia ist ein starkes Setup, aber dein AI-/Tech-Exposure ist bereits hoch. Atlas stuft die Aktie daher nur als 3-4 Wochen Swing ein. Für Core-Zukauf wäre Visa oder ein breiter ETF aktuell portfoliofreundlicher.

## Principle 11 - Atlas Learns From Outcomes

Every recommendation should be trackable.

Atlas should later answer:

- Which strategies worked?
- Which signals were predictive?
- Which sectors produced Alpha?
- Which entries were too early?
- Which stops were too tight?
- Which recommendations added value vs. buy-and-hold?

## Principle 12 - No Auto-Trading in Early Versions

Atlas is a decision-support system. It should not place trades automatically in early versions.

The user makes the final decision.

## Principle 13 - Data Quality Beats Feature Count

A smaller system with reliable data is preferable to a large system with questionable data.

When data is incomplete, stale, derived, or uncertain, Atlas must show this explicitly.

## Principle 14 - Calm Premium Experience

Atlas should feel like Mission Control, not a casino.

Design language:

- calm;
- professional;
- premium;
- concise;
- structured;
- no gamified dopamine triggers;
- no FOMO language.

---

# 3. Mario Investment Profile

## 3.1 Investor identity

Mario's profile is best described as:

> **Strategic Opportunist building his own Investment Office.**

He is not trying to become a frantic trader. He wants a disciplined, intelligent, structured investment cockpit.

Primary identity evolution:

1. Mixed investor profile;
2. Strategic opportunist;
3. Long-term owner/manager of own wealth;
4. Eventually: operator of a personal investment office.

## 3.2 Personal investment priorities

Mario's ranked priorities:

1. Wealth growth;
2. Cashflow;
3. Beating the market;
4. Intellectual challenge;
5. Capital preservation;
6. Minimal time effort.

Interpretation:

- Growth matters.
- Cashflow matters.
- Outperformance matters, but not at the cost of catastrophic drawdowns.
- Atlas should respect intellectual curiosity but reduce unnecessary information overload.

## 3.3 Time commitment

Mario is willing to spend:

- 30-60 minutes per day;
- possibly more, split across the day.

Atlas should support three modes:

1. **Daily Mode** - 5-10 minutes;
2. **Research Mode** - 30-60 minutes;
3. **Review Mode** - weekly/monthly deeper analysis.

## 3.4 Risk response

If Satellite is down 20% in three months, Mario's response is:

- review the strategy;
- follow rules;
- not panic-sell automatically.

Atlas must therefore enforce drawdown reviews and reduce activity during stress.

## 3.5 Success priorities for Atlas

Mario prioritized tool success as:

1. Professional investment cockpit;
2. Additional gains of EUR 5,000-10,000+ per year;
3. Full decision support for wealth;
4. Potential future product/company potential;
5. Beating MSCI World every year.

Interpretation:

Atlas is a cockpit first, alpha tool second, product candidate third.

## 3.6 Preferred themes

Mario is interested in:

- AI;
- cybersecurity;
- energy;
- finance and payments;
- software;
- commodities/resources;
- luxury;
- healthcare/medicine;
- classic blue chips.

Technology and AI remain structurally attractive, but Atlas must not become a Tech-only tool.

## 3.7 Exclusions

Current exclusions:

- tobacco;
- meme stocks.

Future exclusions may include specific jurisdictions, governance profiles, business models or ESG constraints.

## 3.8 Company quality preferences

Approximate preference levels:

| Factor | Preference |
|---|---|
| Market leadership | Medium |
| Moat | Medium-high |
| Recurring revenue | Medium |
| High margins | Medium-high |
| Low debt | Low-medium |
| Insider participation | Medium-high |
| Dividends | Low |
| Innovation | High |
| AI strategy | High |
| Strong management | Medium-high |

Important nuance:

For swing trades, technical quality can dominate long-term business quality. For core holdings, business quality dominates timing.

---

# 4. Financial Freedom Context

## 4.1 Long-term objective

Original objective:

- financial independence in 10-15 years;
- target passive/net cashflow roughly EUR 3,000-4,000 per month;
- ability to reduce work dependency;
- multi-asset wealth structure.

Atlas North Star:

- accelerate this path materially;
- do so without reckless leverage or catastrophic loss risk.

## 4.2 Current project context

Known from the broader project:

- high household income;
- strong savings capacity;
- significant cash position;
- long investment horizon;
- existing ETF, real estate and satellite-trading interest;
- preference for conservative assumptions;
- current need to deploy cash more intelligently;
- existing focus on Austrian tax and personal wealth context.

## 4.3 FIRE Engine view

Atlas should eventually show:

- net worth;
- liquid net worth;
- investable capital;
- cash position;
- FIRE progress;
- FIRE probability;
- projected FIRE date;
- target passive cashflow;
- projected passive cashflow;
- required additional capital;
- required monthly investing rate;
- scenario comparison;
- risk-adjusted progress;
- impact of each recommendation on FIRE path.

## 4.4 FIRE decision translation

Every meaningful portfolio decision should be translatable into FIRE impact.

Examples:

- Investing EUR 10,000 into a broad ETF improves projected FIRE date by X months under base assumptions.
- A EUR 10,000 swing trade has limited FIRE impact unless repeated with positive expectancy.
- Holding too much cash reduces expected FIRE acceleration but may improve optionality.
- Buying a property can improve long-term cashflow but reduce liquidity.

---

# 5. Asset Class Support

## 5.1 Primary asset classes

Priority order:

1. Stocks;
2. ETFs;
3. Real estate;
4. Cash;
5. Precious metals.

## 5.2 Secondary asset classes

6. Private equity;
7. Startups;
8. Bonds;
9. Options;
10. Crypto.

## 5.3 Architecture consequence

Atlas must not be built as a stock-only tool.

Initial MVP may focus on stocks and ETFs, but architecture must allow:

- real estate scorecards;
- cash deployment logic;
- precious metals allocation;
- bonds;
- private investments;
- startup opportunities;
- options as a later, restricted module;
- crypto only as low-priority optional module.

## 5.4 Asset-specific decision rules

Different assets require different rule systems.

Stocks:

- fundamentals;
- chart setup;
- momentum;
- sector strength;
- portfolio concentration.

ETFs:

- exposure;
- index methodology;
- costs;
- diversification;
- overlap;
- liquidity;
- role in core/satellite.

Real estate:

- cashflow;
- yield;
- financing;
- location;
- vacancy risk;
- legal/tax constraints;
- maintenance;
- liquidity impact.

Cash:

- emergency reserve;
- opportunity reserve;
- interest rate;
- deposit protection;
- inflation drag;
- deployment schedule.

Gold/precious metals:

- hedge role;
- crisis diversification;
- correlation;
- position size discipline.

---

# 6. Product Vision

## 6.1 Product name

Working name:

> **Atlas**

Rationale:

- Atlas carries the world; this tool carries the user's wealth strategy.
- The name works across modules: Atlas Daily, Atlas Research, Atlas Portfolio, Atlas FIRE, Atlas Real Estate.
- The name suggests navigation, structure and resilience.

## 6.2 Core product idea

Atlas is a **Personal Wealth Operating System**.

It should answer:

> What should Mario do, review, avoid, or monitor today to move closer to financial independence?

## 6.3 Daily user experience

Desired morning impression after 30 seconds:

> I understand today's opportunities and my wealth development.

Primary daily order:

1. Market traffic light;
2. Top buy candidates;
3. AI summary;
4. News;
5. Portfolio development;
6. Wealth development;
7. Portfolio risk;
8. Financial freedom progress;
9. Calendar.

## 6.4 Candidate policy

Atlas may show up to **10 buy candidates per day**.

If no setup qualifies:

- explicitly state that no candidate met the full quality threshold;
- still show best candidates as watchlist/back-book entries;
- clearly label them as watchlist, not buy.

## 6.5 Interaction model

Atlas should support:

- daily dashboard;
- guided decision cards;
- search by name/ticker/ISIN/WKN;
- natural-language queries;
- back-book deep dives;
- portfolio review;
- journal review;
- weekly/monthly learning.

## 6.6 Product modes

### Atlas Daily

Fast morning mode.

Purpose:

- market regime;
- top opportunities;
- AI summary;
- today's actions;
- portfolio alerts.

### Atlas Research

Deep analysis mode.

Purpose:

- company/ETF analysis;
- sector/theme comparison;
- free text questions;
- back-book research;
- watchlist refinement.

### Atlas Portfolio

Total wealth steering.

Purpose:

- allocation;
- concentration;
- cash deployment;
- rebalance hints;
- risk dashboard.

### Atlas Journal

Decision memory.

Purpose:

- trades;
- recommendations;
- user decisions;
- outcomes;
- lessons.

### Atlas Learn

Feedback loop.

Purpose:

- identify successful strategies;
- evaluate signal quality;
- adjust scoring weights;
- measure Atlas Alpha.

### Atlas FIRE

Goal tracking.

Purpose:

- financial freedom progress;
- target date;
- scenario analysis;
- passive cashflow planning.

### Atlas Real Estate

Property analysis.

Purpose:

- integrate existing real estate scorecard;
- compare property vs ETF/cash;
- liquidity and leverage analysis.

---

# 7. System Architecture

## 7.1 Architecture principle

Atlas should be built as independent engines, not as one monolithic script.

```text
Atlas
├── Data Layer
├── Universe Resolver
├── Market Engine
├── Fundamental Engine
├── Chart Engine
├── Strategy Engine
├── Trade Plan Engine
├── Risk Engine
├── Portfolio Engine
├── FIRE Engine
├── AI Narrative Engine
├── Journal Engine
├── Learning Engine
└── UI Layer
```

## 7.2 Why modular architecture matters

Benefits:

- replace data providers without rewriting the app;
- improve chart engine later without touching FIRE engine;
- run backtests on Strategy Engine independently;
- validate Risk Engine separately;
- use Claude for code modules while ChatGPT reviews logic;
- enable a future Skill to load only relevant rules.

## 7.3 Data Layer

Responsibilities:

- fetch prices;
- fetch fundamentals;
- fetch ETF metadata;
- fetch news;
- fetch earnings dates;
- fetch macro data;
- store snapshots;
- mark data freshness;
- handle source errors;
- normalize identifiers.

Must track:

- provider;
- timestamp;
- currency;
- exchange;
- adjusted/non-adjusted price;
- data confidence;
- missing fields.

## 7.4 Universe Resolver

Purpose:

Resolve user input into investable assets.

Inputs:

- name;
- ticker;
- ISIN;
- WKN;
- sector/theme;
- free-text query.

Outputs:

- canonical ticker;
- asset type;
- exchange;
- currency;
- ISIN/WKN if available;
- company/ETF name;
- ambiguity list if multiple matches;
- data availability status.

This module is critical because European users often search by ISIN or WKN, while many US data APIs are ticker-centric.

## 7.5 Market Engine

Responsibilities:

- determine broad market regime;
- define risk-on/risk-off state;
- monitor VIX/volatility;
- monitor trend of major indices;
- monitor breadth;
- assess sector rotation;
- apply market-regime adjustment to scores.

Possible outputs:

- Risk On;
- Neutral;
- Risk Caution;
- Risk Off;
- Pause.

## 7.6 Fundamental Engine

Responsibilities:

- evaluate business quality;
- growth;
- profitability;
- balance sheet;
- valuation;
- revisions;
- insider/institutional signals;
- sector-specific quality.

Different rules for:

- core candidates;
- swing candidates;
- ETFs;
- defensive assets.

## 7.7 Chart Engine

Responsibilities:

- trend detection;
- market structure;
- support/resistance;
- moving averages;
- volume analysis;
- momentum indicators;
- volatility;
- relative strength;
- entry/stop/target zones;
- invalidation levels.

Chart Engine must produce structured levels, not only a score.

## 7.8 Strategy Engine

Responsibilities:

- assign strategy type;
- evaluate whether the asset fits the intended use;
- decide if setup is buy, watch, avoid or hold;
- apply strategy-specific gates.

## 7.9 Trade Plan Engine

Responsibilities:

- generate entry zone;
- do-not-chase level;
- stop-loss;
- take-profit levels;
- trailing stop logic;
- chance/risk ratio;
- suggested position size;
- holding period;
- invalidation conditions.

## 7.10 Risk Engine

Responsibilities:

- position sizing;
- satellite drawdown tracking;
- exposure caps;
- correlation awareness;
- event risk;
- liquidity risk;
- volatility regime;
- kill-switch logic.

## 7.11 Portfolio Engine

Responsibilities:

- total wealth allocation;
- asset class weights;
- sector weights;
- geographic weights;
- currency exposure;
- cash target;
- portfolio fit score;
- rebalance suggestions.

## 7.12 FIRE Engine

Responsibilities:

- target model;
- projected capital needs;
- passive income gap;
- scenario analysis;
- FIRE probability;
- decision impact.

## 7.13 AI Narrative Engine

Responsibilities:

- synthesize structured engine outputs;
- write concise daily summaries;
- write candidate explanations;
- produce back-book text;
- ask for missing assumptions;
- avoid unsupported claims.

AI Engine must not invent data.

## 7.14 Journal Engine

Responsibilities:

- store recommendations;
- store user decisions;
- store trades;
- track outcomes;
- track rule violations;
- collect notes.

## 7.15 Learning Engine

Responsibilities:

- analyze outcomes;
- compare recommendation vs result;
- measure hit rate;
- measure average gain/loss;
- measure profit factor;
- evaluate strategies by market regime;
- suggest improvements to scoring.

Learning suggestions must be reviewed before becoming rule changes.

---

# 8. Data Contracts

## 8.1 Why data contracts matter

Atlas should not pass vague information between engines. Each engine should produce structured outputs that other modules can consume.

This is critical for:

- testing;
- backtesting;
- AI explainability;
- future Claude implementation;
- future database storage;
- version control of scores.

## 8.2 Candidate object

Minimum candidate fields:

```yaml
candidate:
  asset_id: string
  name: string
  ticker: string
  isin: string | null
  wkn: string | null
  asset_type: stock | etf | commodity | real_estate | cash | other
  exchange: string
  currency: string
  sector: string | null
  theme_tags: list[string]
  price:
    last: number
    timestamp: datetime
    provider: string
  scores:
    asset_score: number
    chart_score: number
    strategy_fit_score: number
    portfolio_fit_score: number
    risk_score: number
    final_atlas_score: number
    confidence: number
  verdict: string
  strategy: string
  trade_plan: object | null
  ai_statement: string
  data_quality: object
```

## 8.3 Trade plan object

```yaml
trade_plan:
  strategy: string
  intent: core | swing | hedge | income | diversification | watchlist | experimental
  entry_zone:
    lower: number
    upper: number
    rationale: list[string]
  do_not_chase_above: number | null
  stop_loss:
    level: number
    type: hard | soft | conditional
    rationale: list[string]
  take_profit:
    tp1:
      level: number
      action: string
      rationale: list[string]
    tp2:
      level: number
      action: string
      rationale: list[string]
    tp3:
      level: number | trailing
      action: string
      rationale: list[string]
  crv:
    tp1: number
    tp2: number
    tp3: number | null
  suggested_position:
    amount_eur: number
    max_amount_eur: number
    risk_eur: number
    risk_pct_satellite: number
  holding_period:
    min_days: number
    max_days: number
  invalidation:
    conditions: list[string]
  portfolio_impact:
    sector_delta: number | null
    theme_delta: number | null
    concentration_warning: string | null
```

## 8.4 Market regime object

```yaml
market_regime:
  state: risk_on | neutral | caution | risk_off | pause
  score: number
  drivers:
    trend: number
    volatility: number
    breadth: number
    sector_rotation: number
    macro_calendar: number
  restrictions:
    allow_new_trades: boolean
    max_position_multiplier: number
    min_score_required: number
    require_stronger_confirmation: boolean
```

## 8.5 Portfolio fit object

```yaml
portfolio_fit:
  score: number
  verdict: improves | neutral | worsens | concentration_risk | diversification_candidate
  current_exposure:
    asset_class: number
    sector: number
    theme: number
    single_name: number
    currency: number
  post_trade_exposure:
    asset_class: number
    sector: number
    theme: number
    single_name: number
    currency: number
  warnings: list[string]
  suggestions: list[string]
```

---

# 9. Atlas Score

## 9.1 Score philosophy

The score is not a truth. It is a structured decision aid.

Atlas must distinguish:

- quality of the asset;
- quality of the chart setup;
- quality of the strategy fit;
- suitability for Mario's portfolio;
- risk-adjusted attractiveness;
- confidence in the data.

## 9.2 Score components v0.2

Initial v0.2 default weighting:

| Component | Weight |
|---|---:|
| Market environment | 15% |
| Quality / fundamentals | 18% |
| Momentum / trend | 17% |
| Chart setup / timing | 20% |
| Risk / volatility / liquidity | 10% |
| Portfolio fit | 15% |
| Catalyst / AI synthesis | 5% |

Rationale for v0.2 adjustment:

- chart setup receives more explicit weight because daily candidates require entry/stop/TP;
- fundamentals remain important but not dominant for swing trades;
- portfolio fit remains significant because Atlas evaluates decisions, not assets.

## 9.3 Strategy-specific weighting

The global weighting is only a default.

### Core Investment weighting

| Component | Weight |
|---|---:|
| Quality / fundamentals | 30% |
| Valuation | 15% |
| Portfolio fit | 20% |
| Market environment | 10% |
| Chart timing | 10% |
| Risk | 10% |
| Catalyst | 5% |

### Satellite Swing weighting

| Component | Weight |
|---|---:|
| Chart setup / timing | 30% |
| Momentum / relative strength | 25% |
| Market environment | 15% |
| Risk / volatility / liquidity | 15% |
| Portfolio fit | 10% |
| Catalyst | 5% |

### Diversification/Hedge weighting

| Component | Weight |
|---|---:|
| Portfolio fit | 30% |
| Market regime | 20% |
| Risk/correlation | 20% |
| Chart timing | 15% |
| Liquidity | 10% |
| Catalyst | 5% |

## 9.4 Score types

Required score types:

- Asset Score;
- Fundamental Score;
- Chart Score;
- Strategy Fit Score;
- Portfolio Fit Score;
- Risk Score;
- Market Regime Score;
- Catalyst Score;
- Final Atlas Score;
- Confidence.

## 9.5 Score vs. confidence

Score answers:

> How attractive is this decision?

Confidence answers:

> How reliable is the assessment?

A candidate can have:

- high score / low confidence: attractive but data weak;
- low score / high confidence: clearly not suitable;
- high score / high confidence: strong candidate;
- medium score / high confidence: watchlist or small position.

## 9.6 Verdict categories

Allowed verdicts:

- Strong Buy;
- Core Candidate;
- Satellite Swing;
- Watchlist;
- Hold;
- Avoid;
- Too Risky;
- Good Asset, Bad Portfolio Fit;
- Diversification Candidate;
- Cash Preferred;
- Wait for Entry;
- Do Not Chase;
- Reduce Exposure;
- Review Required.

## 9.7 Gate rules

Some conditions override scores.

Examples:

- data quality too poor -> no formal recommendation;
- liquidity too low -> avoid for satellite;
- earnings event too close -> downgrade unless Event Driven strategy;
- market regime pause -> no new satellite trades;
- satellite drawdown beyond threshold -> pause new trades;
- stop cannot be placed logically -> watchlist only;
- CRV below minimum -> downgrade;
- portfolio concentration too high -> swing only or avoid.

## 9.8 Minimum thresholds v0.2

Initial thresholds:

| Use case | Minimum Final Score | Minimum Confidence | Notes |
|---|---:|---:|---|
| Strong Buy | 88 | 80 | Requires strong portfolio fit |
| Core Candidate | 82 | 75 | Requires strong fundamentals |
| Satellite Swing | 80 | 75 | Requires complete trade plan |
| Watchlist | 70 | 60 | No action required |
| Avoid / Too Risky | <70 or veto | Any | Explain why |

These are starting values and should be tested.

---

# 10. Strategy Engine

## 10.1 Strategy list

Supported initial strategies:

1. Momentum Pullback;
2. Breakout;
3. Trend Continuation;
4. Mean Reversion;
5. Core Investment;
6. Defensive Allocation;
7. Event Driven;
8. Cash Deployment;
9. ETF Core Allocation;
10. Watchlist/No Trade.

## 10.2 Momentum Pullback

Use when:

- strong uptrend exists;
- price pulls back in controlled way;
- price remains above key moving averages;
- relative strength remains positive;
- support zone or EMA confluence exists;
- CRV is attractive.

Typical horizon:

- 2-8 weeks.

Required chart evidence:

- higher-high/higher-low structure or strong base;
- support or EMA confluence;
- RSI not extremely overbought;
- volume not showing distribution;
- stop can be placed below invalidation.

## 10.3 Breakout

Use when:

- price clears resistance;
- breakout volume confirms;
- base is long enough;
- false breakout risk is manageable;
- market regime supports risk.

Entry options:

- breakout close;
- retest of breakout zone;
- intraday confirmation.

Breakouts in risk-off require reduced size or stronger confirmation.

## 10.4 Trend Continuation

Use when:

- trend is strong;
- pullback is shallow or absent;
- asset shows leadership;
- entry is not overly extended.

If extended:

- reduce size;
- use tighter invalidation;
- prefer wait-for-entry.

## 10.5 Mean Reversion

Use when:

- asset is oversold;
- support is strong;
- reversal signal exists;
- risk can be defined tightly.

This is higher risk and should not be default. It requires stricter stop discipline.

## 10.6 Core Investment

Use when:

- business/ETF quality is high;
- portfolio fit is strong;
- long-term thesis is clear;
- valuation/timing is acceptable;
- position improves FIRE path.

Timing can be less precise than in swing trades, but entry should still avoid obvious overextension.

## 10.7 Defensive Allocation

Use when:

- market risk rises;
- portfolio needs resilience;
- gold/cash/bonds/defensive sectors improve risk profile;
- Atlas wants to preserve capital.

## 10.8 Event Driven

Use around:

- earnings;
- central bank meetings;
- inflation data;
- regulatory decisions;
- product launches;
- sector catalysts.

Event Driven trades require explicit event risk labeling.

## 10.9 Cash Deployment

Use when:

- cash is above target;
- market regime supports gradual deployment;
- FIRE model benefits from investing;
- no better asset-class opportunity exists.

Can recommend:

- ETF tranche;
- wait;
- keep reserve;
- move to higher-yield cash;
- preserve dry powder.

## 10.10 ETF Core Allocation

Use when:

- broad market exposure is desired;
- portfolio needs diversification;
- single-name risk is too high;
- cash should be deployed without active stock selection.

---

# 11. Trade Plan Engine

## 11.1 Mandatory output

Every formal daily candidate must include:

- asset;
- strategy;
- intent;
- verdict;
- entry zone;
- do-not-chase price;
- stop-loss;
- TP1;
- TP2;
- TP3 or trailing stop;
- CRV;
- position size;
- holding period;
- invalidation;
- confidence;
- key reasons;
- key risks;
- portfolio impact;
- back-book link.

## 11.2 Entry logic

Entry should be derived from confluence.

Possible confluence factors:

- EMA20/EMA50/SMA200;
- support/resistance;
- swing low/high;
- Fibonacci retracement;
- VWAP;
- ATR bands;
- volume profile;
- gap fill;
- breakout retest;
- consolidation range;
- trend channel;
- relative strength line;
- candlestick confirmation.

A high-quality entry zone should have at least 2-3 independent supports.

## 11.3 Do-not-chase logic

Atlas must define a price above which the setup is no longer attractive.

Do-not-chase may be based on:

- CRV deterioration;
- distance from EMA20/EMA50;
- ATR extension;
- resistance proximity;
- overbought RSI;
- gap-up risk.

## 11.4 Stop-loss logic

Stop-loss should be below invalidation, not just below comfort.

Potential anchors:

- recent swing low;
- key support;
- EMA50;
- consolidation low;
- ATR distance;
- volume profile shelf;
- breakout failure zone.

Stop must be far enough to avoid normal noise but close enough to protect capital.

## 11.5 Take-profit logic

Take profits should be staged.

Typical framework:

- **TP1**: first logical resistance or 1R-1.5R;
- **TP2**: next major resistance or measured move;
- **TP3**: extended target or trailing stop.

Profit-taking actions:

- partial sell;
- move stop to breakeven;
- trail under EMA20/EMA50;
- hold if trend acceleration continues.

## 11.6 CRV rule

Atlas calculates CRV from:

- entry midpoint;
- stop-loss;
- target levels.

Initial rule:

- TP1 CRV below 1.2 -> weak;
- blended CRV below 1.8 -> downgrade;
- blended CRV above 2.5 -> attractive;
- blended CRV above 3.0 with strong confidence -> strong.

These thresholds should be backtested.

## 11.7 Position sizing

Position size depends on:

- satellite capital;
- stop distance;
- asset volatility;
- confidence;
- market regime;
- portfolio concentration;
- event risk.

Basic formula:

```text
Position Size = Allowed Risk EUR / Stop Distance %
```

Then capped by:

- max single position;
- concentration rules;
- liquidity;
- market regime multiplier;
- event risk multiplier.

## 11.8 Holding period

Every setup requires an expected holding period.

Examples:

- Momentum Pullback: 2-8 weeks;
- Breakout: 1-6 weeks;
- Mean Reversion: days to 3 weeks;
- Core Investment: years;
- Event Driven: defined by event window.

If the expected window expires without thesis confirmation, Atlas should trigger review.

---

# 12. Satellite Portfolio Rules

## 12.1 Capital

Initial maximum satellite pool:

> **EUR 50,000 maximum**

This is not automatically fully deployed. Cash inside Satellite is valid.

## 12.2 Position size

Initial maximum single position:

> **EUR 10,000 or more only when justified**

Interpretation:

- EUR 10,000 is acceptable for high-confidence setups;
- larger positions require stronger confidence, lower stop distance, strong liquidity and acceptable portfolio concentration;
- smaller positions are preferred during risk-off or uncertain regimes.

## 12.3 Loss per trade

Mario selected dynamic risk based on asset/volatility.

Initial risk framework:

| Trade quality | Risk budget |
|---|---:|
| Normal setup | 0.75%-1.0% of Satellite |
| High confidence | up to 1.5% |
| Risk-off small position | 0.25%-0.75% |
| Experimental | 0.25%-0.5% |

At EUR 50,000 Satellite:

- 0.5% = EUR 250;
- 1.0% = EUR 500;
- 1.5% = EUR 750.

## 12.4 Maximum satellite drawdown

Max drawdown before pause:

> **-15%**

At -15% Satellite drawdown:

- new trades paused;
- open trades reviewed;
- strategy review required;
- market regime reassessed;
- no scaling up until recovery/approval.

## 12.5 Annual trade frequency

Target:

> **20-40 completed Satellite trades per year**

Interpretation:

- active but not hectic;
- roughly 2-4 trades per month;
- quality over quantity;
- no need for daily trades.

## 12.6 Rule violations

Atlas should track:

- entry outside zone;
- no stop used;
- position size above recommendation;
- holding beyond thesis window;
- ignored drawdown pause;
- buying during risk-off without reduced size;
- adding to already concentrated exposure.

This is not for blame, but for learning.

---

# 13. Market Regime Rules

## 13.1 Regime states

Atlas should support five states:

1. **Risk On** - normal/opportunistic trading allowed;
2. **Neutral** - selective trading allowed;
3. **Caution** - smaller positions, stricter setups;
4. **Risk Off** - defensive mode, only exceptional trades;
5. **Pause** - no new satellite trades.

## 13.2 Regime inputs

Possible inputs:

- S&P 500 vs SMA200;
- Nasdaq vs SMA200;
- market breadth;
- VIX level/trend;
- sector leadership;
- credit stress indicators;
- macro calendar;
- recent distribution days;
- volatility expansion;
- price structure of major indices.

## 13.3 Risk-off handling

Mario's preference for a 98/100 stock in risk-off:

> Between B and C: small position or asset may still have some priority if exceptionally strong.

Atlas interpretation:

- risk-off does not automatically block everything;
- position size must be reduced;
- minimum score threshold rises;
- chart confirmation must be stronger;
- CRV requirement rises;
- defensive assets become more relevant.

## 13.4 Market multipliers

Initial multipliers:

| Regime | Position multiplier | Minimum score |
|---|---:|---:|
| Risk On | 1.00 | 80 |
| Neutral | 0.75 | 82 |
| Caution | 0.50 | 85 |
| Risk Off | 0.25 | 90 |
| Pause | 0.00 | N/A |

These are v0.2 placeholders and should be backtested.

---

# 14. Portfolio Engine

## 14.1 Role

Atlas may actively support portfolio steering.

It may say:

- cash is above target;
- Tech exposure is high;
- AI exposure is concentrated;
- real estate allocation is below target;
- gold/defensive allocation may improve resilience;
- a trade is suitable only as short-term swing;
- a broad ETF is preferable to another single-name idea.

## 14.2 Correction mode

Mario selected:

> Warnings and suggestions, not forced decisions.

Examples:

- "Tech exposure is high. Consider reducing Nasdaq/AI exposure before adding another AI name."
- "This setup is only suitable as a 3-4 week swing, not as core."
- "A EUR 10,000 purchase would raise sector concentration above target."

## 14.3 Portfolio recommendation types

Atlas can recommend:

- buy candidate;
- watch only;
- wait for entry;
- reduce exposure;
- rebalance hint;
- hold cash;
- add to core ETF;
- add diversification;
- avoid due to concentration;
- review tax/liquidity impact.

## 14.4 Portfolio fit dimensions

Portfolio Fit should consider:

- asset class allocation;
- sector allocation;
- theme exposure;
- single-name concentration;
- currency exposure;
- liquidity;
- correlation;
- FIRE relevance;
- tax friction;
- time horizon;
- overlap with ETFs;
- existing open trades.

## 14.5 Examples

### Example A - Nvidia

- Asset Score: very high;
- Portfolio Fit: reduced if AI/Tech/Nasdaq exposure is high;
- Verdict: Satellite Swing only, small/medium size, defined holding period.

### Example B - Visa

- Asset Score: high;
- Portfolio Fit: potentially strong due to finance/payment theme and lower AI concentration;
- Verdict: Core/Satellite candidate depending on chart.

### Example C - Broad World ETF

- Asset Score: moderate/high;
- Portfolio Fit: high if portfolio needs diversification;
- Verdict: Cash deployment / core allocation.

---

# 15. FIRE Engine

## 15.1 Success metrics

Atlas should judge success by:

1. absolute wealth growth;
2. FIRE target progress;
3. risk-adjusted return.

MSCI World outperformance is useful but not the primary objective.

## 15.2 FIRE dashboard outputs

Required future outputs:

- net worth;
- liquid net worth;
- current investable assets;
- monthly savings/investing capacity;
- target FIRE capital;
- target monthly cashflow;
- current projected cashflow;
- FIRE percentage;
- expected FIRE year;
- pessimistic/base/optimistic scenarios;
- probability estimate;
- gap to target;
- expected impact of current plan.

## 15.3 FIRE action interpretation

Atlas should turn investment actions into FIRE language.

Example:

> Moving EUR 10,000 from excess cash to core ETF improves expected FIRE probability by X under base assumptions, but increases short-term drawdown exposure.

## 15.4 FIRE caution

FIRE projections must be presented as assumptions-based scenarios, not predictions.

Atlas should show assumptions clearly:

- expected return;
- inflation;
- tax assumptions;
- savings rate;
- withdrawal rate;
- real estate cashflow assumptions;
- sequence risk.

---

# 16. UI / UX Vision

## 16.1 Overall feel

Atlas should feel like:

- personal investment desk;
- wealth cockpit;
- Mission Control;
- calm professional dashboard;
- premium but not flashy.

Avoid:

- casino design;
- social trading feeling;
- FOMO language;
- too many alerts;
- cluttered screens.

## 16.2 Mission Control layout

Top priority:

1. Market traffic light;
2. Top candidates;
3. AI summary;
4. News;
5. Portfolio development;
6. Wealth development;
7. Portfolio risk;
8. FIRE progress;
9. Calendar.

## 16.3 Candidate card

Each card should include:

- name/ticker;
- verdict;
- Atlas Score;
- Portfolio Fit;
- Confidence;
- strategy;
- entry zone;
- stop-loss;
- take-profit levels;
- suggested position;
- time horizon;
- why now;
- main risks;
- portfolio warning;
- back-book link.

## 16.4 Back-book view

The back-book should include:

- full score breakdown;
- market regime;
- fundamental analysis;
- chart analysis;
- strategy rationale;
- entry/stop/TP rationale;
- portfolio impact;
- risk calculation;
- event calendar;
- alternative scenarios;
- rejection reasons if not recommended;
- raw source snapshot where possible.

## 16.5 Screener and search

Must support:

- name;
- ticker;
- ISIN;
- WKN;
- sector/theme;
- natural language.

Output:

- full Atlas analysis;
- AI statement;
- verdict;
- score breakdown;
- chart levels;
- portfolio fit;
- back-book.

## 16.6 Mobile experience

iPhone/iPad should support:

- morning dashboard;
- candidate review;
- quick search;
- portfolio alerts;
- journal entry;
- no dense tables unless expandable.

---

# 17. AI Engine

## 17.1 Role

AI should synthesize structured data. It must not invent unsupported facts.

The AI Engine should write:

- daily market summary;
- candidate explanation;
- back-book narrative;
- portfolio warning;
- strategy rationale;
- user-facing plain-language statement.

## 17.2 AI statement structure

Each AI statement should answer:

1. Why this asset?
2. Why now?
3. Which strategy?
4. Why this entry?
5. Why this stop?
6. What could go wrong?
7. How does it affect Mario's portfolio?
8. What action is suggested?

## 17.3 AI agents

Potential specialized agents:

- Market Agent;
- Chart Agent;
- Fundamental Agent;
- Portfolio Agent;
- Risk Agent;
- FIRE Agent;
- News Agent;
- Real Estate Agent;
- Journal Agent;
- QA/Compliance Agent.

## 17.4 AI output rules

AI should:

- be concise in Daily mode;
- be detailed in Back-book mode;
- separate data from interpretation;
- state uncertainty;
- avoid exaggerated certainty;
- avoid hype;
- avoid unsupported claims;
- show missing data.

---

# 18. Data Sources

## 18.1 Priority A

Initial high-value sources:

- Finviz / Finviz Elite;
- TradingView or market data alternative;
- earnings calendar;
- Fear & Greed / sentiment proxy;
- VIX / volatility data;
- price history provider;
- ETF metadata provider;
- ISIN/WKN lookup provider.

## 18.2 Priority B

Additional value:

- OpenInsider;
- 13F filings / hedge fund holdings;
- analyst revisions;
- options data;
- sector rotation data;
- news API.

## 18.3 Priority C

Advanced:

- SEC/company filings;
- macro calendar;
- Fed/inflation/rate data;
- premium fundamental databases;
- portfolio/broker import;
- automated morning reports.

## 18.4 Data governance

Before implementation, check:

- licensing;
- API terms;
- scraping restrictions;
- update frequency;
- currency handling;
- survivorship bias;
- corporate actions;
- adjusted prices;
- timestamp consistency;
- data outage behavior.

## 18.5 Data quality labels

Each output should carry data quality:

- fresh;
- delayed;
- incomplete;
- estimated;
- manual;
- unavailable;
- conflicting.

---

# 19. Technical Product Direction

## 19.1 Development path

Recommended path:

### Phase 1 - Streamlit MVP

Purpose:

- validate scoring;
- validate daily workflow;
- build quickly in Python;
- use manually curated data where needed;
- deploy via hosted URL for iPad/iPhone.

### Phase 2 - Hosted decision cockpit

Purpose:

- stable app;
- daily updates;
- database;
- user portfolio;
- journal;
- AI summaries.

Possible hosting:

- Streamlit Cloud;
- Render;
- Railway;
- later React frontend with backend.

### Phase 3 - Full Atlas OS

Possible architecture:

- React/Next.js frontend;
- Python backend;
- Postgres/Supabase database;
- scheduled jobs;
- authentication;
- AI API integration;
- chart rendering;
- mobile PWA;
- alerts.

## 19.2 Multi-agent development model

Recommended roles:

### ChatGPT

- investment logic;
- product architecture;
- scoring design;
- strategy/risk review;
- documentation;
- QA from user-goal perspective.

### Claude / Claude Code

- code implementation;
- refactoring;
- repository work;
- component build;
- tests;
- long-context codebase editing.

### GitHub

- version control;
- issues;
- pull requests;
- documentation;
- changelog;
- CI checks.

### Atlas Skill

Future reusable Skill containing:

- Atlas Bible;
- strategy rules;
- scoring rules;
- portfolio-fit rules;
- prompts;
- code review checklists;
- safety constraints;
- data handling rules.

## 19.3 Repository standards

Suggested repository structure:

```text
atlas/
├── app/
│   ├── main.py
│   ├── pages/
│   └── components/
├── atlas_core/
│   ├── data/
│   ├── universe/
│   ├── market_engine/
│   ├── fundamental_engine/
│   ├── chart_engine/
│   ├── strategy_engine/
│   ├── trade_plan_engine/
│   ├── risk_engine/
│   ├── portfolio_engine/
│   ├── fire_engine/
│   ├── ai_engine/
│   ├── journal_engine/
│   └── learning_engine/
├── config/
├── tests/
├── docs/
├── specs/
├── prompts/
└── README.md
```

## 19.4 Testing standards

Minimum tests:

- score calculation tests;
- position sizing tests;
- CRV tests;
- stop/TP logic tests;
- portfolio concentration tests;
- data parsing tests;
- no recommendation if required fields missing;
- no new trades during pause state.

---

# 20. Governance and Safety

## 20.1 No auto-trading

Atlas should not place trades automatically in early versions.

Future broker integrations, if ever considered, require separate governance.

## 20.2 Secrets management

Never store in plaintext:

- broker credentials;
- API keys;
- personal finance data;
- portfolio exports;
- tax documents.

Use environment variables or secure secret stores.

## 20.3 No blind code execution

External code, repositories, AI-generated scripts and dependencies must be reviewed before execution.

## 20.4 Financial/legal/tax framing

Atlas provides structured decision support. It is not a guarantee, not personalized licensed financial advice, and not a replacement for tax/legal review.

Austria-specific tax treatment should be displayed only when validated with reliable sources or user-provided assumptions.

## 20.5 Human approval

The user remains final decision maker.

Every trade should require human approval.

## 20.6 Auditability

Atlas should store:

- what was recommended;
- when;
- based on what data;
- which version of scoring;
- what the user decided;
- outcome.

This enables learning and accountability.

---

# 21. Backtesting and Learning

## 21.1 Why this matters

Atlas must not only sound intelligent. It must prove over time that it improves decision quality.

## 21.2 Recommendation tracking

For every recommendation:

- date;
- asset;
- strategy;
- score;
- confidence;
- entry zone;
- stop;
- TP levels;
- market regime;
- portfolio fit;
- user action;
- outcome after 5/10/20/60 trading days;
- max favorable excursion;
- max adverse excursion;
- rule violations.

## 21.3 Metrics

Track:

- hit rate;
- average winner;
- average loser;
- profit factor;
- expectancy;
- max drawdown;
- average holding time;
- alpha vs benchmark;
- risk-adjusted return;
- recommendation-to-action conversion;
- missed opportunity cost;
- stop accuracy;
- TP accuracy.

## 21.4 Learning process

Monthly review:

1. summarize performance;
2. identify best/worst strategy;
3. identify bad rules;
4. propose changes;
5. do not auto-change rules;
6. document accepted changes in changelog.

## 21.5 Avoid overfitting

Atlas must avoid tuning rules only to recent trades.

Rule changes require:

- enough sample size;
- plausible causal logic;
- regime awareness;
- documentation;
- review.

---

# 22. Sprint Roadmap

## Sprint 0 - Documentation and foundation

Deliverables:

- ATLAS_BIBLE_v0.2_PRO.md;
- ATLAS_SPEC_v0.1.md;
- initial repository structure;
- Claude build prompt;
- initial backlog;
- MVP acceptance criteria.

## Sprint 1 - Investment Engine MVP

Deliverables:

- market traffic light;
- ticker universe/watchlist;
- price history ingestion;
- technical indicators;
- basic fundamentals placeholder;
- Atlas Score v0.2;
- top 10 candidates;
- trade plan generation;
- Streamlit Mission Control.

Acceptance criteria:

- user can load dashboard;
- user sees market regime;
- user sees up to 10 candidates;
- each candidate has score, strategy, entry, stop, TP, position suggestion;
- candidates can be exported;
- no candidate is recommended without stop and CRV;
- system clearly marks data quality.

## Sprint 2 - Screener and search

Deliverables:

- search by name/ticker;
- ISIN/WKN resolution where possible;
- single asset analysis;
- AI statement placeholder;
- back-book page;
- watchlist save.

## Sprint 3 - Portfolio Engine MVP

Deliverables:

- manual portfolio input;
- asset class allocation;
- sector exposure;
- cash position;
- portfolio fit score;
- warnings;
- rebalance hints.

## Sprint 4 - AI Summary and Back-book

Deliverables:

- AI daily summary;
- candidate explanation;
- risk explanation;
- why accepted/rejected;
- structured back-book.

## Sprint 5 - Journal and Learning

Deliverables:

- journal;
- recommendation tracking;
- outcome tracking;
- hit rate;
- profit factor;
- strategy performance.

## Sprint 6 - FIRE and Real Estate

Deliverables:

- FIRE progress dashboard;
- scenario model;
- real estate scorecard integration;
- cash deployment recommendations.

## Sprint 7 - Mobile/Premium UI

Deliverables:

- iPad/iPhone optimized interface;
- PWA behavior;
- morning report;
- alerts;
- premium Mission Control design.

---

# 23. MVP Scope v0.2

## 23.1 MVP should include

- Mission Control page;
- Market Regime Engine basic version;
- Watchlist universe;
- Chart Engine basic indicators;
- Strategy Engine v0.1;
- Trade Plan Engine v0.1;
- Atlas Score;
- Candidate table/cards;
- manual search by ticker/name;
- basic config file;
- export function;
- documentation.

## 23.2 MVP should not include yet

- broker connection;
- automatic trading;
- options trading;
- complex tax engine;
- full real estate module;
- paid-data dependency unless explicitly chosen;
- full AI agent orchestration;
- highly polished React UI.

## 23.3 MVP philosophy

The MVP should prove that Atlas can create **useful daily decision plans**.

It does not need perfect design. It needs:

- good logic;
- clear output;
- reliable calculations;
- explainability;
- discipline.

---

# 24. Claude / Coding Agent Build Prompt

This section can be used as an initial prompt for Claude Code or a coding agent.

```text
You are helping build Atlas, a personal Wealth Operating System for Mario.

Read ATLAS_BIBLE_v0.2_PRO.md first. Do not build a generic stock screener.

Atlas must evaluate decisions, not only assets. Every candidate requires:
- strategy
- entry zone
- do-not-chase level
- stop-loss
- TP1/TP2/TP3 or trailing stop
- CRV
- suggested position size
- holding period
- portfolio impact placeholder
- confidence
- data quality

Initial implementation should be a Streamlit MVP with modular Python package structure:
- data layer
- market engine
- chart engine
- strategy engine
- trade plan engine
- risk engine
- scoring engine
- UI components

Do not implement broker trading.
Do not store secrets in code.
Do not make unsupported financial claims.
Use clear tests for scoring, CRV, position sizing, and no-recommendation cases.
Prioritize correctness and maintainability over UI polish.
```

---

# 25. Atlas Skill Direction

Atlas is skill-tauglich.

A future Atlas Skill should help ChatGPT consistently act as Atlas product strategist, reviewer and specification maintainer.

## 25.1 Skill contents

Potential skill structure:

```text
atlas-skill/
├── SKILL.md
├── references/
│   ├── ATLAS_BIBLE.md
│   ├── scoring_rules.md
│   ├── trade_plan_rules.md
│   ├── portfolio_fit_rules.md
│   ├── risk_governance.md
│   └── claude_prompts.md
├── scripts/
│   ├── validate_candidate_json.py
│   └── score_schema_check.py
└── agents/
    └── openai.yaml
```

## 25.2 Skill triggers

The skill should trigger when the user asks to:

- continue Atlas development;
- review Atlas code;
- design Atlas scoring;
- create Atlas specs;
- evaluate a trade candidate under Atlas rules;
- generate Claude build prompts;
- update Atlas Bible or Specs.

## 25.3 Skill caution

The skill must not turn Atlas into a financial advice automation tool. It should support structured analysis and project development.

---

# 26. Open Questions

## 26.1 Product questions

1. Exact target allocation across asset classes.
2. Exact cash reserve target.
3. Exact Core/Satellite/Experimental percentages.
4. Preferred hosting path after MVP.
5. Whether Atlas remains private or could become product.
6. Exact UI design system.
7. Whether to implement notifications.
8. Whether to implement broker import.

## 26.2 Data questions

1. Final price data provider.
2. Fundamental data provider.
3. ISIN/WKN resolver.
4. ETF metadata provider.
5. News provider.
6. Earnings data source.
7. Data licensing constraints.
8. Historical data for backtesting.

## 26.3 Investment questions

1. Exact max Tech exposure.
2. Exact max AI exposure.
3. Max single stock exposure across total wealth.
4. Cash reserve target.
5. Gold target allocation.
6. Real estate target allocation.
7. ETF core target allocation.
8. Austria tax display assumptions.

## 26.4 Strategy questions

1. Minimum CRV by strategy.
2. Default ATR stop multipliers.
3. Strategy-specific holding periods.
4. Earnings blackout rules.
5. Gap risk handling.
6. Whether to include short strategies.
7. Whether options remain analysis-only.

---

# 27. Current Working Definitions

## Atlas

Personal Wealth Operating System for Mario.

## Mission Control

Main dashboard summarizing market, opportunities, portfolio, wealth, risk and actions.

## Atlas Score

Composite score combining market, fundamentals, momentum, chart setup, risk, portfolio fit and catalyst factors.

## Asset Score

Score of the asset on standalone attractiveness.

## Portfolio Fit

Measure of whether an asset improves or worsens Mario's total portfolio relative to current exposure and goals.

## Decision Score

Final recommendation quality after applying asset, chart, risk, strategy, portfolio and market context.

## Confidence

Reliability of the assessment based on data quality, signal confluence and regime clarity.

## Back-book

Full research and reasoning layer behind a recommendation.

## Satellite

Active opportunity/trading portfolio, max initial capital EUR 50,000.

## FIRE

Financial independence / financial freedom objective.

## Do-not-chase price

Price level above which the setup no longer has sufficient CRV or timing quality.

---

# 28. Immediate Next Steps

Recommended next actions:

1. Create `ATLAS_SPEC_v0.1.md` from this Bible.
2. Define initial repository structure.
3. Refactor existing MVP into Atlas module names.
4. Create config files for risk rules and scoring weights.
5. Implement basic Market Engine.
6. Implement basic Chart Engine.
7. Implement Trade Plan Engine with entry/stop/TP/CRV.
8. Implement Candidate Card UI.
9. Add manual search by ticker/name.
10. Define ISIN/WKN data approach.
11. Create Claude Sprint 1 task prompt.
12. Add tests for CRV, position sizing and no-recommendation logic.
13. Create first sample daily output using a static watchlist.

---

# 29. v0.2 Pro Review Notes

## 29.1 What was strong in v0.1

- The vision was clear.
- The distinction between Atlas as Wealth OS and stock screener was strong.
- FIRE-first philosophy was explicit.
- Core modules were already identified.
- Trade plan requirement was already present.
- Portfolio fit was correctly treated as central.
- Multi-agent direction was already identified.

## 29.2 What needed strengthening

- Engine boundaries needed more precision.
- Data contracts were missing.
- Risk governance needed clearer states and thresholds.
- Score vs confidence needed separation.
- Strategy-specific scoring was missing.
- Chart-technical entry logic needed stronger structure.
- MVP acceptance criteria were missing.
- Backtesting/learning process needed more rigor.
- Claude/coding prompt needed explicit constraints.
- Skill direction needed an initial structure.

## 29.3 v0.2 conclusion

Atlas is now sufficiently defined to move from concept into specification and implementation.

The next artifact should be:

> **ATLAS_SPEC_v0.1.md**

The next technical action should be:

> **Refactor the MVP into Atlas architecture and implement Sprint 1 Investment Engine.**

---

# 30. Changelog

## v0.2 Pro Review - 2026-07-04

Added:

- professional document structure;
- stronger principles;
- data contracts;
- modular engine architecture;
- score vs confidence distinction;
- strategy-specific scoring weights;
- trade plan engine details;
- chart-technical framework;
- risk regime states;
- market multipliers;
- satellite risk framework;
- portfolio fit dimensions;
- FIRE decision translation;
- AI output rules;
- data governance;
- testing standards;
- backtesting and learning framework;
- MVP scope and acceptance criteria;
- Claude build prompt;
- Atlas Skill direction;
- Pro review notes.

## v0.1 - 2026-07-04

Initial foundation draft created from the Atlas concept workshop.

Captured:

- vision;
- user profile;
- investment philosophy;
- asset class priorities;
- module architecture;
- scoring logic;
- trade engine requirements;
- portfolio rules;
- FIRE orientation;
- data source ideas;
- technology direction;
- roadmap.
