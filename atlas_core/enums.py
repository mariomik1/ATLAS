from enum import Enum


class AssetClass(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    PRECIOUS_METAL = "precious_metal"
    PRIVATE_EQUITY = "private_equity"
    STARTUP = "startup"
    BOND = "bond"
    OPTION = "option"
    CRYPTO = "crypto"


class InvestmentIntent(str, Enum):
    CORE = "core"
    SWING = "swing"
    DEFENSIVE = "defensive"
    DIVERSIFICATION = "diversification"
    INCOME = "income"
    WATCH = "watch"
    SPECULATION = "speculation"


class MarketRegime(str, Enum):
    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    RISK_OFF = "risk_off"
    UNKNOWN = "unknown"


class Strategy(str, Enum):
    MOMENTUM_PULLBACK = "momentum_pullback"
    BREAKOUT = "breakout"
    TREND_CONTINUATION = "trend_continuation"
    MEAN_REVERSION = "mean_reversion"
    CORE_INVESTMENT = "core_investment"
    DEFENSIVE_ALLOCATION = "defensive_allocation"
    CASH_DEPLOYMENT = "cash_deployment"
    WATCHLIST_ONLY = "watchlist_only"


class Verdict(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    SWING_CANDIDATE = "swing_candidate"
    CORE_CANDIDATE = "core_candidate"
    WATCH = "watch"
    HOLD = "hold"
    AVOID = "avoid"
    GOOD_ASSET_BAD_FIT = "good_asset_bad_portfolio_fit"


class DataQualityLevel(str, Enum):
    LIVE = "live"
    DELAYED = "delayed"
    SAMPLE = "sample"
    PARTIAL = "partial"
    MISSING = "missing"
