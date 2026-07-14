from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


@dataclass(frozen=True)
class QuoteContext:
    symbol: str
    current_price: Any = "n/a"
    currency: str = "n/a"
    exchange: str = "n/a"
    source: str = "n/a"
    data_quality: str = "unknown"


def _valid(value: Any) -> bool:
    return value not in (None, "", "n/a", "None")


def _round_price(value: Any) -> Any:
    try:
        return round(float(value), 2)
    except Exception:
        return value if _valid(value) else "n/a"


def quote_from_payload(payload: dict[str, Any]) -> QuoteContext:
    asset = payload.get("asset", {}) or {}
    market_data = payload.get("market_data", {}) or {}
    quote = payload.get("quote", {}) or {}
    data_quality = payload.get("data_quality", {}) or {}

    symbol = (
        payload.get("symbol")
        or asset.get("symbol")
        or quote.get("symbol")
        or "n/a"
    )

    current_price = (
        payload.get("current_price")
        or payload.get("last_price")
        or payload.get("price")
        or asset.get("current_price")
        or asset.get("last_price")
        or market_data.get("current_price")
        or market_data.get("last_close")
        or quote.get("price")
        or quote.get("regular_market_price")
        or "n/a"
    )

    currency = (
        payload.get("currency")
        or asset.get("currency")
        or market_data.get("currency")
        or quote.get("currency")
        or "USD"
    )

    exchange = (
        payload.get("exchange")
        or asset.get("exchange")
        or asset.get("exchange_name")
        or market_data.get("exchange")
        or quote.get("exchange")
        or quote.get("full_exchange_name")
        or "n/a"
    )

    quality_level = (
        data_quality.get("level")
        if isinstance(data_quality, dict)
        else data_quality
    ) or "unknown"

    return QuoteContext(
        symbol=str(symbol).upper(),
        current_price=_round_price(current_price),
        currency=str(currency),
        exchange=str(exchange),
        source="payload",
        data_quality=str(quality_level),
    )


def fetch_yfinance_quote(symbol: str) -> QuoteContext:
    clean_symbol = str(symbol).upper().strip()

    if yf is None:
        return QuoteContext(
            symbol=clean_symbol,
            current_price="n/a",
            currency="n/a",
            exchange="yfinance unavailable",
            source="yfinance",
            data_quality="error",
        )

    try:
        ticker = yf.Ticker(clean_symbol)

        current_price = None
        currency = None

        try:
            fast_info = ticker.fast_info
            current_price = getattr(fast_info, "last_price", None)
            currency = getattr(fast_info, "currency", None)
        except Exception:
            pass

        raw_info = {}
        try:
            raw_info = ticker.info or {}
        except Exception:
            raw_info = {}

        if not _valid(current_price):
            current_price = (
                raw_info.get("currentPrice")
                or raw_info.get("regularMarketPrice")
                or raw_info.get("previousClose")
            )

        if not _valid(currency):
            currency = raw_info.get("currency", "n/a")

        exchange = (
            raw_info.get("fullExchangeName")
            or raw_info.get("exchange")
            or raw_info.get("market")
            or "yfinance / default listing"
        )

        return QuoteContext(
            symbol=clean_symbol,
            current_price=_round_price(current_price),
            currency=str(currency) if _valid(currency) else "n/a",
            exchange=str(exchange) if _valid(exchange) else "yfinance / default listing",
            source="yfinance",
            data_quality="delayed",
        )
    except Exception:
        return QuoteContext(
            symbol=clean_symbol,
            current_price="n/a",
            currency="n/a",
            exchange="yfinance / unavailable",
            source="yfinance",
            data_quality="error",
        )


def get_quote_context(payload: dict[str, Any]) -> QuoteContext:
    base = quote_from_payload(payload)
    live = fetch_yfinance_quote(base.symbol)

    current_price = live.current_price if _valid(live.current_price) else base.current_price
    currency = live.currency if _valid(live.currency) else base.currency
    exchange = live.exchange if _valid(live.exchange) else base.exchange

    data_quality = live.data_quality if live.data_quality != "error" else base.data_quality
    source = "yfinance" if _valid(live.current_price) else base.source

    return QuoteContext(
        symbol=base.symbol,
        current_price=current_price,
        currency=currency,
        exchange=exchange,
        source=source,
        data_quality=data_quality,
    )
