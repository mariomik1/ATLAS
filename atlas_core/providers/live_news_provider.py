from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, List

from atlas_core.enums import DataQualityLevel
from atlas_core.models import CatalystEvent, DataQuality, NewsItem
from atlas_core.providers.http_client import JsonHttpClient
from atlas_core.providers.news_provider import CsvSampleNewsProvider, NewsProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.time_utils import utc_now


class _LiveNewsBase(NewsProvider):
    name = "live_news_base"

    def __init__(
        self,
        *,
        api_key: str | None,
        settings: dict,
        fallback_provider: CsvSampleNewsProvider | None = None,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        http_client: JsonHttpClient | None = None,
        live_enabled: bool = False,
        ttl_seconds: int | float = 7200,
        stale_allowed: bool = True,
    ):
        self.api_key = api_key
        self.settings = settings
        self.fallback_provider = fallback_provider or CsvSampleNewsProvider(settings)
        self.cache = cache or JsonFileCache(settings.get("cache", {}).get("base_dir", "data/cache"))
        self.audit = audit or FetchAuditLogger(settings.get("audit", {}).get("fetch_log_path", "data/cache/fetch_audit.jsonl"))
        self.http_client = http_client or JsonHttpClient()
        self.live_enabled = live_enabled
        self.ttl_seconds = ttl_seconds
        self.stale_allowed = stale_allowed

    @property
    def ready(self) -> bool:
        return bool(self.live_enabled and self.api_key)

    def get_events_for_symbol(self, symbol: str, limit: int | None = None) -> List[CatalystEvent]:
        return self.fallback_provider.get_events_for_symbol(symbol, limit=limit)

    def _fallback_news(self, symbol: str, limit: int | None) -> List[NewsItem]:
        return self.fallback_provider.get_news_for_symbol(symbol, limit=limit)

    def _fallback_market_news(self, symbols: Iterable[str] | None, limit: int | None) -> List[NewsItem]:
        return self.fallback_provider.get_market_news(symbols=symbols, limit=limit)

    def _cache_or_fetch(self, namespace: str, key: str, fetcher, resource: str) -> Any:
        cached = self.cache.get(namespace, key, ttl_seconds=self.ttl_seconds)
        if cached.hit and cached.payload is not None:
            self.audit.log(provider=self.name, resource=resource, status="cache_hit", cache_hit=True, data_quality="live_or_delayed_cache", message="Loaded news provider response from cache.")
            return cached.payload
        if not self.ready:
            raise RuntimeError(f"{self.name} disabled or API key missing.")
        stale_payload = cached.payload if cached.expired and cached.payload is not None else None
        try:
            payload = fetcher()
        except Exception as exc:
            if stale_payload is not None and self.stale_allowed:
                self.audit.log(provider=self.name, resource=resource, status="provider_failed_stale_cache_used", cache_hit=True, data_quality="partial", message=f"News fetch failed; stale cache used: {type(exc).__name__}: {exc}")
                return stale_payload
            self.audit.log(provider=self.name, resource=resource, status="provider_fetch_failed", cache_hit=False, data_quality="missing", message=f"News fetch failed: {type(exc).__name__}: {exc}")
            raise
        self.cache.set(namespace, key, payload, metadata={"provider": self.name, "resource": resource})
        self.audit.log(provider=self.name, resource=resource, status="provider_fetch_success", cache_hit=False, data_quality="live_or_delayed", message="Fetched and cached live news provider response.")
        return payload

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if not value:
            return utc_now()
        try:
            raw = str(value).replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return utc_now()

    def _quality(self, issues: list[str]) -> DataQuality:
        return DataQuality(level=DataQualityLevel.DELAYED, provider=self.name, as_of=utc_now(), issues=issues)


class MarketauxNewsProvider(_LiveNewsBase):
    name = "marketaux"
    base_url = "https://api.marketaux.com/v1/news/all"

    def get_news_for_symbol(self, symbol: str, limit: int | None = None) -> List[NewsItem]:
        symbol = symbol.upper().strip()
        max_items = limit or int(self.settings.get("news", {}).get("max_items_per_symbol", 6))
        if not self.ready:
            return self._fallback_news(symbol, max_items)
        try:
            payload = self._cache_or_fetch(
                "news",
                f"marketaux:symbol:{symbol}:limit:{max_items}",
                lambda: self.http_client.get_json(self.base_url, params={"api_token": self.api_key, "symbols": symbol, "limit": max_items, "language": "en"}).payload,
                f"symbol/{symbol}",
            )
            return self._items_from_payload(payload, symbol=symbol)[:max_items] or self._fallback_news(symbol, max_items)
        except Exception:
            return self._fallback_news(symbol, max_items)

    def get_market_news(self, symbols: Iterable[str] | None = None, limit: int | None = None) -> List[NewsItem]:
        max_items = limit or int(self.settings.get("news", {}).get("max_market_news", 8))
        if not self.ready:
            return self._fallback_market_news(symbols=symbols, limit=max_items)
        keyword = ",".join(symbols or ["SPY", "QQQ", "ACWI"])
        try:
            payload = self._cache_or_fetch(
                "news",
                f"marketaux:market:{keyword}:limit:{max_items}",
                lambda: self.http_client.get_json(self.base_url, params={"api_token": self.api_key, "symbols": keyword, "limit": max_items, "language": "en"}).payload,
                "market",
            )
            return self._items_from_payload(payload, symbol="MARKET")[:max_items] or self._fallback_market_news(symbols=symbols, limit=max_items)
        except Exception:
            return self._fallback_market_news(symbols=symbols, limit=max_items)

    def _items_from_payload(self, payload: Any, *, symbol: str) -> list[NewsItem]:
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        items: list[NewsItem] = []
        for row in rows:
            entities = row.get("entities") if isinstance(row, dict) else []
            entity_symbols = [str(e.get("symbol", "")).upper() for e in entities if isinstance(e, dict)]
            inferred_symbol = symbol if symbol != "MARKET" else (entity_symbols[0] if entity_symbols else "MARKET")
            sentiment = row.get("sentiment_score")
            if sentiment is None and entities:
                sentiments = [e.get("sentiment_score") for e in entities if isinstance(e, dict) and isinstance(e.get("sentiment_score"), (int, float))]
                sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            relevance = row.get("match_score") or row.get("relevance_score") or 70
            title = str(row.get("title") or "")
            description = str(row.get("description") or row.get("snippet") or "")
            risk_flags = []
            if (sentiment or 0) < -0.35:
                risk_flags.append("negative_news_sentiment")
            items.append(NewsItem(
                symbol=inferred_symbol,
                title=title,
                summary=description,
                source=str(row.get("source") or "Marketaux"),
                url=row.get("url"),
                published_at=self._parse_datetime(row.get("published_at")),
                category="company" if inferred_symbol != "MARKET" else "market",
                event_type="news",
                sentiment_score=max(-1, min(1, float(sentiment or 0))),
                relevance_score=max(0, min(100, float(relevance or 70))),
                impact_score=max(0, min(100, float(relevance or 70))),
                risk_flag=bool(risk_flags),
                topics=["marketaux", "news"],
                risk_flags=risk_flags,
                data_quality=self._quality(["Marketaux live/delayed news normalized by Atlas. Verify source before trading."]),
            ))
        return sorted(items, key=lambda item: item.published_at, reverse=True)


class NewsApiProvider(_LiveNewsBase):
    name = "newsapi"
    base_url = "https://newsapi.org/v2/everything"

    def get_news_for_symbol(self, symbol: str, limit: int | None = None) -> List[NewsItem]:
        symbol = symbol.upper().strip()
        max_items = limit or int(self.settings.get("news", {}).get("max_items_per_symbol", 6))
        if not self.ready:
            return self._fallback_news(symbol, max_items)
        query = symbol
        try:
            payload = self._cache_or_fetch(
                "news",
                f"newsapi:symbol:{symbol}:limit:{max_items}",
                lambda: self.http_client.get_json(self.base_url, params={"apiKey": self.api_key, "q": query, "language": "en", "sortBy": "publishedAt", "pageSize": max_items}).payload,
                f"symbol/{symbol}",
            )
            return self._items_from_payload(payload, symbol=symbol)[:max_items] or self._fallback_news(symbol, max_items)
        except Exception:
            return self._fallback_news(symbol, max_items)

    def get_market_news(self, symbols: Iterable[str] | None = None, limit: int | None = None) -> List[NewsItem]:
        max_items = limit or int(self.settings.get("news", {}).get("max_market_news", 8))
        if not self.ready:
            return self._fallback_market_news(symbols=symbols, limit=max_items)
        query = "stock market OR Nasdaq OR S&P 500"
        try:
            payload = self._cache_or_fetch(
                "news",
                f"newsapi:market:{max_items}",
                lambda: self.http_client.get_json(self.base_url, params={"apiKey": self.api_key, "q": query, "language": "en", "sortBy": "publishedAt", "pageSize": max_items}).payload,
                "market",
            )
            return self._items_from_payload(payload, symbol="MARKET")[:max_items] or self._fallback_market_news(symbols=symbols, limit=max_items)
        except Exception:
            return self._fallback_market_news(symbols=symbols, limit=max_items)

    def _items_from_payload(self, payload: Any, *, symbol: str) -> list[NewsItem]:
        rows = payload.get("articles", []) if isinstance(payload, dict) else []
        items = []
        for row in rows:
            title = str(row.get("title") or "")
            desc = str(row.get("description") or row.get("content") or "")
            items.append(NewsItem(
                symbol=symbol,
                title=title,
                summary=desc,
                source=str((row.get("source") or {}).get("name") or "NewsAPI"),
                url=row.get("url"),
                published_at=self._parse_datetime(row.get("publishedAt")),
                category="market" if symbol == "MARKET" else "company",
                event_type="news",
                sentiment_score=0.0,
                relevance_score=65,
                impact_score=60,
                topics=["newsapi", "news"],
                data_quality=self._quality(["NewsAPI response has no native financial sentiment; Atlas uses neutral sentiment until AI/news scoring is upgraded."]),
            ))
        return sorted(items, key=lambda item: item.published_at, reverse=True)
