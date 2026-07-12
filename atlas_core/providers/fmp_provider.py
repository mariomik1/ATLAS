from __future__ import annotations

import json
from datetime import date
from typing import Any, Callable, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import (
    CompanyProfile,
    DataQuality,
    FundamentalContext,
    FundamentalMetrics,
    IdentifierMatch,
    SearchResult,
)
from atlas_core.providers.fundamentals_provider import CsvSampleFundamentalsProvider, FundamentalsProvider
from atlas_core.providers.identifier_provider import CsvIdentifierProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.indicators import clamp
from atlas_core.utils.time_utils import utc_now

JsonFetcher = Callable[[str, dict[str, str] | None], Any]


class FMPApiClient:
    """Small FMP HTTP client with injectable fetcher for tests.

    This client intentionally keeps request construction transparent. Every call
    appends the API key as a query parameter and returns decoded JSON. Provider
    classes decide what to cache, how to normalize responses and when to fall
    back to sample data.
    """

    base_url = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str, fetch_json: JsonFetcher | None = None, timeout_seconds: int = 20):
        self.api_key = api_key
        self.fetch_json = fetch_json or self._default_fetch_json
        self.timeout_seconds = timeout_seconds

    def get(self, endpoint: str, **params: Any) -> Any:
        endpoint = endpoint.strip("/")
        params = {key: value for key, value in params.items() if value is not None}
        params["apikey"] = self.api_key
        url = f"{self.base_url}/{endpoint}?{urlencode(params)}"
        return self.fetch_json(url, None)

    def _default_fetch_json(self, url: str, headers: dict[str, str] | None = None) -> Any:
        request = Request(url, headers=headers or {"User-Agent": "Atlas/0.6B"})
        with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec - controlled provider URL
            return json.loads(response.read().decode("utf-8"))


class FMPIdentifierProvider:
    """FMP-backed ticker/name/ISIN search with local fallback.

    Supported live endpoints in Sprint 6B:
    - search-name
    - search-symbol
    - search-isin

    WKN is not a native FMP identifier endpoint in this sprint. WKN-like queries
    are resolved via local sample/master fallback or aliases until a licensed
    WKN source is added.
    """

    name = "fmp_identifier"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        live_enabled: bool = False,
        fallback_provider: CsvIdentifierProvider | None = None,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        ttl_seconds: int = 2_592_000,
        fetch_json: JsonFetcher | None = None,
    ):
        self.api_key = api_key
        self.live_enabled = live_enabled
        self.fallback_provider = fallback_provider or CsvIdentifierProvider()
        self.cache = cache or JsonFileCache()
        self.audit = audit or FetchAuditLogger()
        self.ttl_seconds = ttl_seconds
        self.client = FMPApiClient(api_key, fetch_json=fetch_json) if api_key else None
        self._last_quality: DataQuality = DataQuality(level=DataQualityLevel.SAMPLE, provider="fmp_identifier+fallback")

    def resolve(self, query: str) -> Optional[IdentifierMatch]:
        result = self.search(query, limit=1)
        return result.matches[0] if result.matches else None

    def search(self, query: str, limit: int = 10) -> SearchResult:
        normalized = query.strip()
        if not normalized:
            return SearchResult(query=query, matches=[], data_quality=self._quality(DataQualityLevel.MISSING, "empty_query"))

        if not self.live_enabled or not self.client:
            result = self.fallback_provider.search(query, limit=limit)
            quality = self._quality(
                DataQualityLevel.SAMPLE,
                "FMP identifier provider disabled or missing API key; used local fallback.",
            )
            self._last_quality = quality
            return SearchResult(query=query, matches=result.matches, data_quality=quality)

        cache_key = f"fmp_identifier:{normalized}:{limit}"
        cached = self.cache.get("identifiers", cache_key, ttl_seconds=self.ttl_seconds)
        if cached.hit:
            matches = [self._payload_to_match(item, query=query, provider="fmp_identifier_cache") for item in cached.payload or []]
            quality = self._quality(DataQualityLevel.DELAYED, "Identifier result served from cache.", provider="fmp_identifier_cache")
            for match in matches:
                match.data_quality.provider = "fmp_identifier_cache"
            self.audit.log(provider=self.name, resource="identifiers", status="cache_hit", cache_hit=True, data_quality=quality.level)
            self._last_quality = quality
            return SearchResult(query=query, matches=matches[:limit], data_quality=quality)

        try:
            payload = self._fetch_identifier_payload(normalized)
            matches = [self._payload_to_match(item, query=query, provider=self.name) for item in payload]
            matches = [match for match in matches if match.symbol]
            matches.sort(key=lambda m: m.confidence, reverse=True)
            self.cache.set("identifiers", cache_key, [m.model_dump(mode="json") for m in matches[:limit]], metadata={"provider": self.name})
            quality = self._quality(DataQualityLevel.DELAYED, "FMP identifier data fetched live/delayed and normalized.")
            self.audit.log(provider=self.name, resource="identifiers", status="provider_fetch_success", data_quality=quality.level)
            self._last_quality = quality
            if matches:
                return SearchResult(query=query, matches=matches[:limit], data_quality=quality)
        except Exception as exc:  # pragma: no cover - exercised through fake failure tests
            self.audit.log(provider=self.name, resource="identifiers", status="provider_fetch_failed", data_quality="sample", message=str(exc))

        fallback = self.fallback_provider.search(query, limit=limit)
        quality = self._quality(DataQualityLevel.SAMPLE, "FMP lookup failed or returned no matches; used local fallback.")
        self._last_quality = quality
        return SearchResult(query=query, matches=fallback.matches, data_quality=quality)

    def metadata_for_symbol(self, symbol: str) -> dict[str, str]:
        if hasattr(self.fallback_provider, "metadata_for_symbol"):
            return self.fallback_provider.metadata_for_symbol(symbol)
        return {}

    def _fetch_identifier_payload(self, query: str) -> list[dict[str, Any]]:
        assert self.client is not None
        endpoint = "search-isin" if self._looks_like_isin(query) else "search-symbol" if len(query) <= 8 and query.replace(".", "").isalnum() else "search-name"
        if endpoint == "search-isin":
            raw = self.client.get(endpoint, isin=query)
        else:
            raw = self.client.get(endpoint, query=query)
        return self._ensure_list(raw)

    def _payload_to_match(self, item: dict[str, Any], *, query: str, provider: str) -> IdentifierMatch:
        if "symbol" in item and "asset_class" in item:
            match = IdentifierMatch(**item)
            match.provider = provider
            match.data_quality.provider = provider
            return match
        symbol = str(item.get("symbol") or item.get("ticker") or "").strip().upper()
        name = str(item.get("name") or item.get("companyName") or symbol).strip() or symbol
        query_norm = query.strip().lower()
        symbol_norm = symbol.lower()
        name_norm = name.lower()
        isin = self._clean(item.get("isin"))
        match_type = "provider"
        confidence = 76.0
        if query_norm == symbol_norm:
            match_type, confidence = "ticker", 98.0
        elif isin and query_norm == isin.lower():
            match_type, confidence = "isin", 98.0
        elif query_norm == name_norm:
            match_type, confidence = "name", 94.0
        elif query_norm and query_norm in name_norm:
            match_type, confidence = "partial_name", 78.0
        quality = self._quality(DataQualityLevel.DELAYED, "FMP identifier record; validate before execution.", provider=provider)
        return IdentifierMatch(
            query=query,
            symbol=symbol,
            name=name,
            asset_class=self._asset_class(item),
            match_type=match_type,
            confidence=confidence,
            exchange=self._clean(item.get("exchangeShortName") or item.get("exchange") or item.get("stockExchange")),
            country=self._clean(item.get("country")),
            currency=str(item.get("currency") or "USD"),
            isin=isin,
            provider=provider,
            data_quality=quality,
        )

    @staticmethod
    def _looks_like_isin(query: str) -> bool:
        q = query.strip().upper()
        return len(q) == 12 and q[:2].isalpha() and q[2:11].isalnum() and q[-1].isalnum()

    @staticmethod
    def _ensure_list(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [v for v in value if isinstance(v, dict)]
        if isinstance(value, dict):
            return [value]
        return []

    @staticmethod
    def _asset_class(item: dict[str, Any]) -> AssetClass:
        raw = str(item.get("type") or item.get("assetClass") or item.get("securityType") or "stock").lower()
        if "etf" in raw or "fund" in raw:
            return AssetClass.ETF
        return AssetClass.STOCK

    @staticmethod
    def _clean(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _quality(self, level: DataQualityLevel, issue: str, provider: str | None = None) -> DataQuality:
        return DataQuality(level=level, provider=provider or self.name, as_of=utc_now(), issues=[issue])


class FMPFundamentalsProvider(CsvSampleFundamentalsProvider):
    """FMP-backed fundamentals provider with cache and sample fallback.

    The provider fetches profile, ratios-ttm, key-metrics-ttm,
    income-statement-growth and analyst-estimates when enabled. It normalizes
    the response into Atlas' internal FundamentalContext before any engine uses
    it.
    """

    name = "fmp_fundamentals"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        live_enabled: bool = False,
        fallback_provider: CsvSampleFundamentalsProvider | None = None,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        ttl_seconds: int = 604_800,
        fetch_json: JsonFetcher | None = None,
    ):
        self.api_key = api_key
        self.live_enabled = live_enabled
        self.fallback_provider = fallback_provider or CsvSampleFundamentalsProvider()
        self.cache = cache or JsonFileCache()
        self.audit = audit or FetchAuditLogger()
        self.ttl_seconds = ttl_seconds
        self.client = FMPApiClient(api_key, fetch_json=fetch_json) if api_key else None

    def get_context(self, symbol: str) -> FundamentalContext:
        normalized = symbol.strip().upper()
        if not self.live_enabled or not self.client:
            return self._fallback(normalized, "FMP fundamentals disabled or missing API key; used sample fallback.")

        cache_key = f"fmp_fundamentals:{normalized}"
        cached = self.cache.get("fundamentals", cache_key, ttl_seconds=self.ttl_seconds)
        if cached.hit:
            context = self._payload_to_context(normalized, cached.payload or {}, provider="fmp_fundamentals_cache")
            self.audit.log(provider=self.name, resource="fundamentals", status="cache_hit", cache_hit=True, data_quality=context.data_quality.level)
            return context

        try:
            payload = self._fetch_fundamentals_payload(normalized)
            self.cache.set("fundamentals", cache_key, payload, metadata={"provider": self.name})
            context = self._payload_to_context(normalized, payload, provider=self.name)
            self.audit.log(provider=self.name, resource="fundamentals", status="provider_fetch_success", data_quality=context.data_quality.level)
            return context
        except Exception as exc:  # pragma: no cover - covered by failure tests with fake fetcher
            self.audit.log(provider=self.name, resource="fundamentals", status="provider_fetch_failed", data_quality="sample", message=str(exc))
            return self._fallback(normalized, f"FMP fundamentals failed; used sample fallback. Error: {exc}")

    def _fetch_fundamentals_payload(self, symbol: str) -> dict[str, Any]:
        assert self.client is not None
        return {
            "profile": self.client.get("profile", symbol=symbol),
            "ratios_ttm": self.client.get("ratios-ttm", symbol=symbol),
            "key_metrics_ttm": self.client.get("key-metrics-ttm", symbol=symbol),
            "growth": self.client.get("income-statement-growth", symbol=symbol),
            "analyst_estimates": self.client.get("analyst-estimates", symbol=symbol, period="annual", page=0, limit=3),
        }

    def _payload_to_context(self, symbol: str, payload: dict[str, Any], *, provider: str) -> FundamentalContext:
        profile_raw = self._first(payload.get("profile"))
        ratios = self._first(payload.get("ratios_ttm"))
        key_metrics = self._first(payload.get("key_metrics_ttm"))
        growth = self._first(payload.get("growth"))
        analyst = self._first(payload.get("analyst_estimates"))
        quality = DataQuality(
            level=DataQualityLevel.DELAYED,
            provider=provider,
            as_of=utc_now(),
            issues=["FMP fundamentals are normalized provider data; validate important fields before execution."],
        )
        name = self._clean(profile_raw.get("companyName") or profile_raw.get("companyName") or profile_raw.get("name")) or symbol
        profile = CompanyProfile(
            symbol=symbol,
            name=name,
            asset_class=AssetClass.ETF if "etf" in str(profile_raw.get("type", "")).lower() else AssetClass.STOCK,
            sector=self._clean(profile_raw.get("sector")),
            industry=self._clean(profile_raw.get("industry")),
            country=self._clean(profile_raw.get("country")),
            exchange=self._clean(profile_raw.get("exchangeShortName") or profile_raw.get("exchange")),
            currency=str(profile_raw.get("currency") or "USD"),
            isin=self._clean(profile_raw.get("isin")),
            website=self._clean(profile_raw.get("website")),
            description=self._clean(profile_raw.get("description")),
            data_quality=quality,
        )
        metrics = FundamentalMetrics(
            symbol=symbol,
            market_cap_usd=self._pick_float(profile_raw, key_metrics, keys=["mktCap", "marketCap", "marketCapTTM"]),
            revenue_growth_yoy_pct=self._pct(self._pick_float(growth, keys=["growthRevenue", "revenueGrowth", "growthRevenueTTM"])),
            eps_growth_yoy_pct=self._pct(self._pick_float(growth, keys=["growthEPSDiluted", "epsGrowth", "growthEPS"])),
            gross_margin_pct=self._pct(self._pick_float(ratios, keys=["grossProfitMarginTTM", "grossProfitMargin"])),
            operating_margin_pct=self._pct(self._pick_float(ratios, keys=["operatingProfitMarginTTM", "operatingProfitMargin"])),
            net_margin_pct=self._pct(self._pick_float(ratios, keys=["netProfitMarginTTM", "netProfitMargin"])),
            roe_pct=self._pct(self._pick_float(ratios, key_metrics, keys=["returnOnEquityTTM", "returnOnEquity", "roeTTM", "roe"])),
            roic_pct=self._pct(self._pick_float(key_metrics, ratios, keys=["roicTTM", "roic", "returnOnInvestedCapitalTTM"])),
            debt_to_equity=self._pick_float(ratios, key_metrics, keys=["debtEquityRatioTTM", "debtToEquityTTM", "debtToEquity"]),
            free_cash_flow_yield_pct=self._pct(self._pick_float(key_metrics, keys=["freeCashFlowYieldTTM", "freeCashFlowYield"])),
            pe_ttm=self._pick_float(ratios, key_metrics, profile_raw, keys=["priceEarningsRatioTTM", "peRatioTTM", "peRatio", "priceEarningsRatio"]),
            forward_pe=self._pick_float(profile_raw, analyst, keys=["forwardPE", "forwardPe", "estimatedPe"]),
            peg_ratio=self._pick_float(key_metrics, ratios, keys=["pegRatioTTM", "pegRatio"]),
            dividend_yield_pct=self._pct(self._pick_float(ratios, key_metrics, profile_raw, keys=["dividendYieldTTM", "dividendYield"])),
            beta=self._pick_float(profile_raw, key_metrics, keys=["beta"]),
            analyst_revision_score=60.0 if analyst else None,
            data_quality=quality,
        )
        quality_score = self._quality_score(metrics)
        growth_score = self._growth_score(metrics)
        profitability_score = self._profitability_score(metrics)
        balance_sheet_score = self._balance_sheet_score(metrics)
        valuation_score = self._valuation_score(metrics)
        ownership_score = self._ownership_score(metrics)
        overall = clamp(
            0.20 * quality_score
            + 0.20 * growth_score
            + 0.25 * profitability_score
            + 0.15 * balance_sheet_score
            + 0.12 * valuation_score
            + 0.08 * ownership_score
        )
        context = FundamentalContext(
            symbol=symbol,
            profile=profile,
            metrics=metrics,
            quality_score=round(quality_score, 2),
            growth_score=round(growth_score, 2),
            profitability_score=round(profitability_score, 2),
            balance_sheet_score=round(balance_sheet_score, 2),
            valuation_score=round(valuation_score, 2),
            ownership_score=round(ownership_score, 2),
            overall_score=round(overall, 2),
            classification=self._classification(overall),
            data_quality=quality,
        )
        context.reasons = self._reasons(context)
        context.risks = self._risks(context)
        context.missing_fields = self._missing(metrics)
        if context.missing_fields:
            context.data_quality.issues.append(f"Missing normalized fields: {', '.join(context.missing_fields[:5])}.")
        return context

    def _fallback(self, symbol: str, issue: str) -> FundamentalContext:
        context = self.fallback_provider.get_context(symbol)
        context.data_quality.issues.append(issue)
        context.data_quality.provider = f"{self.name}+{context.data_quality.provider}"
        return context

    @staticmethod
    def _first(value: Any) -> dict[str, Any]:
        if isinstance(value, list):
            return value[0] if value and isinstance(value[0], dict) else {}
        if isinstance(value, dict):
            return value
        return {}

    @staticmethod
    def _pick_float(*dicts: dict[str, Any], keys: list[str]) -> Optional[float]:
        for data in dicts:
            for key in keys:
                value = data.get(key)
                if value is None or value == "":
                    continue
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _pct(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if -2 <= value <= 2:
            return value * 100
        return value

    @staticmethod
    def _clean(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
