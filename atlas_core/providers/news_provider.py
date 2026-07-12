from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from atlas_core.config_loader import PROJECT_ROOT
from atlas_core.enums import DataQualityLevel
from atlas_core.models import CatalystEvent, DataQuality, NewsItem
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.env_loader import get_secret, load_env_file
from atlas_core.utils.time_utils import utc_now

JsonFetcher = Callable[[str, dict[str, str] | None], Any]


class NewsProvider(ABC):
    name: str

    @abstractmethod
    def get_news_for_symbol(self, symbol: str, limit: int | None = None) -> List[NewsItem]:
        raise NotImplementedError

    @abstractmethod
    def get_market_news(self, symbols: Iterable[str] | None = None, limit: int | None = None) -> List[NewsItem]:
        raise NotImplementedError

    @abstractmethod
    def get_events_for_symbol(self, symbol: str, limit: int | None = None) -> List[CatalystEvent]:
        raise NotImplementedError


class CsvSampleNewsProvider(NewsProvider):
    """Offline news/events provider used as deterministic fallback."""

    name = "csv_sample_news"

    def __init__(self, settings: dict):
        news_cfg = settings.get("news", {})
        configured_path = news_cfg.get("csv_path", "data/samples/news_items.csv")
        configured_events_path = news_cfg.get("events_csv_path", "data/samples/events.csv")
        self.csv_path = self._project_path(configured_path)
        self.events_csv_path = self._project_path(configured_events_path)
        self.max_items_per_symbol = int(news_cfg.get("max_items_per_symbol", 6))
        self.min_relevance_score = float(news_cfg.get("min_relevance_score", 0))
        self.market_news_symbols = [str(x).upper() for x in news_cfg.get("market_news_symbols", ["MARKET"])]
        self.quality = DataQuality(
            level=DataQualityLevel(news_cfg.get("data_quality_level", "sample")),
            provider=self.name,
            as_of=utc_now(),
            issues=["Offline sample news/events. Not live news."],
        )
        self._items = self._load_items()
        self._events = self._load_events()

    @staticmethod
    def _project_path(value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    def _load_items(self) -> List[NewsItem]:
        if not self.csv_path.exists():
            return []
        df = pd.read_csv(self.csv_path)
        if df.empty:
            return []
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
        items: list[NewsItem] = []
        for _, row in df.iterrows():
            relevance = float(row.get("relevance_score", 50) or 50)
            if relevance < self.min_relevance_score:
                continue
            risk_flag = self._to_bool(row.get("risk_flag", False))
            risk_flags = [str(row.get("event_type", "risk"))] if risk_flag else []
            items.append(
                NewsItem(
                    symbol=str(row["symbol"]).upper(),
                    published_at=row["published_at"].to_pydatetime(),
                    title=str(row.get("title", "")),
                    summary=str(row.get("summary", "")),
                    source=str(row.get("source", self.name)),
                    url=str(row.get("url", "")) or None,
                    category=str(row.get("category", "company")),
                    event_type=str(row.get("event_type", "news")),
                    sentiment_score=float(row.get("sentiment_score", 0) or 0),
                    relevance_score=relevance,
                    impact_score=float(row.get("impact_score", 50) or 50),
                    risk_flag=risk_flag,
                    topics=[str(row.get("category", "company")), str(row.get("event_type", "news"))],
                    risk_flags=risk_flags,
                    data_quality=self.quality,
                )
            )
        return sorted(items, key=lambda x: x.published_at, reverse=True)

    def _load_events(self) -> List[CatalystEvent]:
        if not self.events_csv_path.exists():
            return []
        df = pd.read_csv(self.events_csv_path)
        if df.empty:
            return []
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
        events: list[CatalystEvent] = []
        for _, row in df.iterrows():
            events.append(
                CatalystEvent(
                    symbol=str(row["symbol"]).upper(),
                    event_date=row["event_date"],
                    event_type=str(row.get("event_type", "event")),
                    description=str(row.get("description", "")),
                    importance=str(row.get("importance", "medium")),
                    source=str(row.get("source", self.name)),
                    data_quality=self.quality,
                )
            )
        return sorted(events, key=lambda x: x.event_date)

    @staticmethod
    def _to_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y"}

    def get_news_for_symbol(self, symbol: str, limit: int | None = None) -> List[NewsItem]:
        symbol = symbol.upper().strip()
        max_items = limit if limit is not None else self.max_items_per_symbol
        return [item for item in self._items if item.symbol == symbol][:max_items]

    def get_market_news(self, symbols: Iterable[str] | None = None, limit: int | None = None) -> List[NewsItem]:
        target_symbols = [s.upper() for s in (symbols or self.market_news_symbols)]
        max_items = limit if limit is not None else self.max_items_per_symbol
        return [item for item in self._items if item.symbol in target_symbols][:max_items]

    def get_events_for_symbol(self, symbol: str, limit: int | None = None) -> List[CatalystEvent]:
        symbol = symbol.upper().strip()
        events = [event for event in self._events if event.symbol == symbol]
        return events[:limit] if limit is not None else events


class LiveNewsProviderBase(NewsProvider):
    """Base class for controlled live/delayed news providers.

    Network calls are executed only when live_enabled=True and provider-specific
    keys are present where required. Every fetch uses cache + audit logging and
    falls back to the CSV provider on failure.
    """

    name = "live_news_base"

    def __init__(
        self,
        settings: dict,
        *,
        api_key: str | None,
        live_enabled: bool,
        fallback_provider: CsvSampleNewsProvider | None = None,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        fetch_json: JsonFetcher | None = None,
    ):
        self.settings = settings
        self.news_cfg = settings.get("news", {})
        self.api_key = api_key
        self.live_enabled = live_enabled
        self.fallback_provider = fallback_provider or CsvSampleNewsProvider(settings)
        self.cache = cache or JsonFileCache(settings.get("cache", {}).get("base_dir", "data/cache"))
        self.audit = audit or FetchAuditLogger(settings.get("audit", {}).get("fetch_log_path", "data/cache/fetch_audit.jsonl"))
        self.fetch_json = fetch_json or self._default_fetch_json
        self.max_items_per_symbol = int(self.news_cfg.get("max_items_per_symbol", 6))
        self.max_market_news = int(self.news_cfg.get("max_market_news", 8))
        self.ttl_seconds = int(float(self.news_cfg.get("cache_ttl_minutes", 120)) * 60)

    @property
    def ready(self) -> bool:
        return bool(self.live_enabled and self.api_key)

    def get_news_for_symbol(self, symbol: str, limit: int | None = None) -> List[NewsItem]:
        if not self.ready:
            return self.fallback_provider.get_news_for_symbol(symbol, limit=limit)
        return self._cached_fetch(kind="symbol", symbol=symbol.upper().strip(), limit=limit or self.max_items_per_symbol)

    def get_market_news(self, symbols: Iterable[str] | None = None, limit: int | None = None) -> List[NewsItem]:
        if not self.ready:
            return self.fallback_provider.get_market_news(symbols=symbols, limit=limit)
        return self._cached_fetch(kind="market", symbol="MARKET", limit=limit or self.max_market_news)

    def get_events_for_symbol(self, symbol: str, limit: int | None = None) -> List[CatalystEvent]:
        return self.fallback_provider.get_events_for_symbol(symbol, limit=limit)

    def _cached_fetch(self, *, kind: str, symbol: str, limit: int) -> List[NewsItem]:
        cache_key = f"{self.name}:{kind}:{symbol}:{limit}"
        cached = self.cache.get("news", cache_key, ttl_seconds=self.ttl_seconds)
        if cached.hit and cached.payload is not None:
            self.audit.log(provider=self.name, resource=f"news/{kind}/{symbol}", status="cache_hit", cache_hit=True, data_quality="delayed")
            return [NewsItem(**item) for item in cached.payload][:limit]
        stale_payload = cached.payload if cached.expired and cached.payload is not None else None
        try:
            payload = self._fetch_payload(kind=kind, symbol=symbol, limit=limit)
            items = self._normalize_payload(payload, requested_symbol=symbol, kind=kind)[:limit]
            self.cache.set("news", cache_key, [item.model_dump(mode="json") for item in items], metadata={"provider": self.name, "kind": kind})
            self.audit.log(provider=self.name, resource=f"news/{kind}/{symbol}", status="provider_fetch_success", cache_hit=False, data_quality="delayed")
            if items:
                return items
        except Exception as exc:  # pragma: no cover - fake failure tests cover via provider behavior
            self.audit.log(provider=self.name, resource=f"news/{kind}/{symbol}", status="provider_fetch_failed", cache_hit=False, data_quality="sample", message=str(exc))
        if stale_payload:
            return [NewsItem(**item) for item in stale_payload][:limit]
        return self.fallback_provider.get_market_news(limit=limit) if kind == "market" else self.fallback_provider.get_news_for_symbol(symbol, limit=limit)

    def _fetch_payload(self, *, kind: str, symbol: str, limit: int) -> Any:
        raise NotImplementedError

    def _normalize_payload(self, payload: Any, *, requested_symbol: str, kind: str) -> list[NewsItem]:
        raise NotImplementedError

    def _get_json(self, url: str, headers: dict[str, str] | None = None) -> Any:
        return self.fetch_json(url, headers)

    @staticmethod
    def _default_fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
        request = Request(url, headers=headers or {"User-Agent": "Atlas/technical-mvp"})
        with urlopen(request, timeout=20) as response:  # nosec - provider URLs are controlled by adapters
            return json.loads(response.read().decode("utf-8"))

    def _quality(self, provider: str) -> DataQuality:
        return DataQuality(
            level=DataQualityLevel.DELAYED,
            provider=provider,
            as_of=utc_now(),
            issues=["Live/delayed provider data. Verify source and timestamp before any action."],
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime:
        if value is None:
            return utc_now()
        text = str(value).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return utc_now()
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    @staticmethod
    def _score_sentiment(raw: Any) -> float:
        if raw is None:
            return 0.0
        if isinstance(raw, (int, float)):
            value = float(raw)
            return max(-1, min(1, value if abs(value) <= 1 else value / 100))
        text = str(raw).lower()
        if "positive" in text:
            return 0.35
        if "negative" in text:
            return -0.35
        return 0.0


class MarketauxNewsProvider(LiveNewsProviderBase):
    name = "marketaux_news"

    def _fetch_payload(self, *, kind: str, symbol: str, limit: int) -> Any:
        base = self.news_cfg.get("marketaux_base_url", "https://api.marketaux.com/v1/news/all")
        params = {"api_token": self.api_key, "limit": limit, "language": "en"}
        if kind == "symbol":
            params["symbols"] = symbol
        else:
            params["industries"] = "Technology,Financial Services,Energy,Healthcare"
        return self._get_json(f"{base}?{urlencode(params)}", {"User-Agent": "Atlas/technical-mvp"})

    def _normalize_payload(self, payload: Any, *, requested_symbol: str, kind: str) -> list[NewsItem]:
        records = payload.get("data", []) if isinstance(payload, dict) else []
        items: list[NewsItem] = []
        for record in records:
            entities = record.get("entities") or []
            symbol = requested_symbol if kind == "symbol" else "MARKET"
            if entities and kind == "symbol":
                symbol = str(entities[0].get("symbol") or requested_symbol).upper()
            sentiment = self._score_sentiment(record.get("sentiment"))
            score = max(abs(sentiment) * 100, 55)
            items.append(
                NewsItem(
                    symbol=symbol,
                    title=str(record.get("title") or ""),
                    summary=str(record.get("description") or record.get("snippet") or ""),
                    source=str(record.get("source") or "marketaux"),
                    url=record.get("url"),
                    published_at=self._parse_dt(record.get("published_at")),
                    category="market" if kind == "market" else "company",
                    event_type="news",
                    sentiment_score=sentiment,
                    relevance_score=float(record.get("match_score") or score),
                    impact_score=score,
                    risk_flag=sentiment < -0.35,
                    topics=["provider", "marketaux"],
                    risk_flags=["negative_news"] if sentiment < -0.35 else [],
                    data_quality=self._quality(self.name),
                )
            )
        return items


class NewsAPINewsProvider(LiveNewsProviderBase):
    name = "newsapi_news"

    def _fetch_payload(self, *, kind: str, symbol: str, limit: int) -> Any:
        base = self.news_cfg.get("newsapi_base_url", "https://newsapi.org/v2/everything")
        query = symbol if kind == "symbol" else "stock market OR Nasdaq OR S&P 500"
        params = {"q": query, "language": "en", "sortBy": "publishedAt", "pageSize": limit, "apiKey": self.api_key}
        return self._get_json(f"{base}?{urlencode(params)}", {"User-Agent": "Atlas/technical-mvp"})

    def _normalize_payload(self, payload: Any, *, requested_symbol: str, kind: str) -> list[NewsItem]:
        records = payload.get("articles", []) if isinstance(payload, dict) else []
        items: list[NewsItem] = []
        for record in records:
            title = str(record.get("title") or "")
            description = str(record.get("description") or "")
            sentiment = self._keyword_sentiment(f"{title} {description}")
            items.append(
                NewsItem(
                    symbol=requested_symbol if kind == "symbol" else "MARKET",
                    title=title,
                    summary=description,
                    source=str((record.get("source") or {}).get("name") or "newsapi"),
                    url=record.get("url"),
                    published_at=self._parse_dt(record.get("publishedAt")),
                    category="market" if kind == "market" else "company",
                    event_type="news",
                    sentiment_score=sentiment,
                    relevance_score=65,
                    impact_score=60 + abs(sentiment) * 25,
                    risk_flag=sentiment < -0.35,
                    topics=["provider", "newsapi"],
                    risk_flags=["negative_news"] if sentiment < -0.35 else [],
                    data_quality=self._quality(self.name),
                )
            )
        return items

    @staticmethod
    def _keyword_sentiment(text: str) -> float:
        text = text.lower()
        negative = any(word in text for word in ["lawsuit", "cut", "miss", "downgrade", "probe", "warning"])
        positive = any(word in text for word in ["beats", "upgrade", "raises", "growth", "record", "strong"])
        return -0.35 if negative and not positive else 0.30 if positive and not negative else 0.0


class FMPNewsProvider(LiveNewsProviderBase):
    name = "fmp_news"

    def _fetch_payload(self, *, kind: str, symbol: str, limit: int) -> Any:
        base = self.news_cfg.get("fmp_base_url", "https://financialmodelingprep.com/stable")
        endpoint = "stock-news" if kind == "symbol" else "general-news"
        params = {"apikey": self.api_key, "limit": limit}
        if kind == "symbol":
            params["symbols"] = symbol
        return self._get_json(f"{base}/{endpoint}?{urlencode(params)}", {"User-Agent": "Atlas/technical-mvp"})

    def _normalize_payload(self, payload: Any, *, requested_symbol: str, kind: str) -> list[NewsItem]:
        records = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
        items: list[NewsItem] = []
        for record in records:
            title = str(record.get("title") or "")
            text = f"{title} {record.get('text') or record.get('summary') or ''}"
            sentiment = NewsAPINewsProvider._keyword_sentiment(text)
            items.append(
                NewsItem(
                    symbol=str(record.get("symbol") or requested_symbol if kind == "symbol" else "MARKET").upper(),
                    title=title,
                    summary=str(record.get("text") or record.get("summary") or ""),
                    source=str(record.get("site") or record.get("publisher") or "fmp"),
                    url=record.get("url"),
                    published_at=self._parse_dt(record.get("publishedDate") or record.get("published_at")),
                    category="market" if kind == "market" else "company",
                    event_type="news",
                    sentiment_score=sentiment,
                    relevance_score=70,
                    impact_score=62 + abs(sentiment) * 25,
                    risk_flag=sentiment < -0.35,
                    topics=["provider", "fmp"],
                    risk_flags=["negative_news"] if sentiment < -0.35 else [],
                    data_quality=self._quality(self.name),
                )
            )
        return items


def build_news_provider(settings: dict, *, fetch_json: JsonFetcher | None = None) -> NewsProvider:
    cfg = settings.get("news", {})
    provider = str(cfg.get("provider", "csv_sample")).lower()
    live_enabled = bool(cfg.get("live_providers_enabled", False))
    fallback = CsvSampleNewsProvider(settings)
    env = load_env_file()
    if provider == "marketaux":
        return MarketauxNewsProvider(settings, api_key=get_secret("MARKETAUX_API_KEY", env), live_enabled=live_enabled, fallback_provider=fallback, fetch_json=fetch_json)
    if provider == "newsapi":
        return NewsAPINewsProvider(settings, api_key=get_secret("NEWSAPI_API_KEY", env), live_enabled=live_enabled, fallback_provider=fallback, fetch_json=fetch_json)
    if provider == "fmp":
        return FMPNewsProvider(settings, api_key=get_secret("FMP_API_KEY", env), live_enabled=live_enabled, fallback_provider=fallback, fetch_json=fetch_json)
    return fallback


class FutureLiveNewsProvider(LiveNewsProviderBase):
    name = "future_live_news"


# Backward-compatible provider name used by existing tests.
class CsvNewsProvider(CsvSampleNewsProvider):
    def __init__(self, csv_path: str = "data/samples/news_items.csv", events_csv_path: str | None = None):
        settings = {
            "news": {
                "csv_path": csv_path,
                "events_csv_path": events_csv_path or "data/samples/events.csv",
                "max_items_per_symbol": 6,
                "min_relevance_score": 0,
                "market_news_symbols": ["MARKET"],
                "data_quality_level": "sample",
            }
        }
        super().__init__(settings)
        self.events_csv_path = Path(events_csv_path or "data/samples/events.csv")
        if not self.events_csv_path.is_absolute():
            self.events_csv_path = PROJECT_ROOT / self.events_csv_path

    def news_for_symbol(self, symbol: str, limit: int | None = None) -> List[NewsItem]:
        return self.get_news_for_symbol(symbol, limit=limit)

    def events_for_symbol(self, symbol: str):
        return self.get_events_for_symbol(symbol)
