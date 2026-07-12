from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional
from urllib.request import Request, urlopen

from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import DataQuality, IdentifierMatch, SearchResult
from atlas_core.providers.identifier_provider import CsvIdentifierProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.time_utils import utc_now

OpenFigiFetcher = Callable[[str, dict[str, str], Any], Any]


class OpenFigiIdentifierProvider:
    """Controlled OpenFIGI identifier mapping/search provider.

    Network calls are attempted only when live_enabled=True. The provider uses
    cache/audit wrappers and falls back to the local identifier master when
    disabled, keyless, rate-limited or otherwise unavailable.
    """

    name = "openfigi"
    base_url = "https://api.openfigi.com"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        fallback_provider: CsvIdentifierProvider | None = None,
        ttl_seconds: int | float = 2592000,
        live_enabled: bool = False,
        stale_allowed: bool = True,
        timeout: float = 12.0,
        fetch_json: Callable[[str, dict[str, str], Any], Any] | None = None,
    ):
        self.api_key = api_key
        self.cache = cache or JsonFileCache("data/cache")
        self.audit = audit or FetchAuditLogger("data/cache/fetch_audit.jsonl")
        self.fallback_provider = fallback_provider or CsvIdentifierProvider()
        self.ttl_seconds = ttl_seconds
        self.live_enabled = live_enabled
        self.stale_allowed = stale_allowed
        self.timeout = timeout
        self.fetch_json = fetch_json
        self.fetch_json = fetch_json

    @property
    def ready(self) -> bool:
        # OpenFIGI works without an API key at lower limits, but Atlas still uses
        # explicit live_enabled to avoid accidental network calls.
        return bool(self.live_enabled)

    def resolve(self, query: str) -> Optional[IdentifierMatch]:
        result = self.search(query, limit=1)
        return result.matches[0] if result.matches else None

    def search(self, query: str, limit: int = 10) -> SearchResult:
        cleaned = query.strip()
        if not cleaned:
            return SearchResult(query=query, matches=[], data_quality=self._quality(DataQualityLevel.MISSING, ["Empty search query."]))
        if not self.ready:
            fallback = self.fallback_provider.search(query, limit=limit)
            fallback.data_quality.provider = f"{fallback.data_quality.provider}+openfigi_disabled_fallback"
            fallback.data_quality.issues.append("OpenFIGI identifier provider is disabled by config.")
            return fallback
        try:
            matches = self._live_search(cleaned, limit=limit)
        except Exception as exc:
            fallback = self.fallback_provider.search(query, limit=limit)
            fallback.data_quality.provider = f"{fallback.data_quality.provider}+openfigi_failed_fallback"
            fallback.data_quality.level = DataQualityLevel.PARTIAL
            fallback.data_quality.issues.append(f"OpenFIGI identifier search failed: {type(exc).__name__}: {exc}")
            return fallback
        return SearchResult(
            query=query,
            matches=matches[:limit],
            data_quality=self._quality(
                DataQualityLevel.DELAYED if matches else DataQualityLevel.MISSING,
                ["OpenFIGI identifier search/mapping used. Validate exchange and listing before execution."],
            ),
        )

    def _live_search(self, query: str, limit: int) -> list[IdentifierMatch]:
        if self._looks_like_isin(query):
            payload = self._post_json("/v3/mapping", [{"idType": "ID_ISIN", "idValue": query.upper(), "marketSecDes": "Equity"}], resource=f"openfigi/mapping/isin/{query.upper()}")
            records = self._records_from_mapping_payload(payload)
            match_type = "isin"
        elif self._looks_like_symbol(query):
            payload = self._post_json("/v3/mapping", [{"idType": "TICKER", "idValue": query.upper(), "marketSecDes": "Equity"}], resource=f"openfigi/mapping/ticker/{query.upper()}")
            records = self._records_from_mapping_payload(payload)
            match_type = "symbol"
        else:
            payload = self._post_json("/v3/search", {"query": query, "marketSecDes": "Equity"}, resource=f"openfigi/search/{query}")
            records = self._records_from_search_payload(payload)
            match_type = "provider"
        return self._records_to_matches(query, records, match_type=match_type)[:limit]

    def _post_json(self, endpoint: str, payload: Any, *, resource: str) -> Any:
        cache_key = f"{endpoint}:{json.dumps(payload, sort_keys=True)}"
        cached = self.cache.get("identifiers", cache_key, ttl_seconds=self.ttl_seconds)
        if cached.hit and cached.payload is not None:
            self.audit.log(provider=self.name, resource=resource, status="cache_hit", cache_hit=True, data_quality="live_cache", message="Loaded OpenFIGI response from cache.")
            return cached.payload
        stale_payload = cached.payload if cached.expired and cached.payload is not None else None
        try:
            response = self._http_post_json(endpoint, payload)
        except Exception as exc:
            if stale_payload is not None and self.stale_allowed:
                self.audit.log(provider=self.name, resource=resource, status="provider_failed_stale_cache_used", cache_hit=True, data_quality="partial", message=f"OpenFIGI fetch failed; stale cache used: {type(exc).__name__}: {exc}")
                return stale_payload
            self.audit.log(provider=self.name, resource=resource, status="provider_fetch_failed", cache_hit=False, data_quality="missing", message=f"OpenFIGI fetch failed: {type(exc).__name__}: {exc}")
            raise
        self.cache.set("identifiers", cache_key, response, metadata={"provider": self.name, "endpoint": endpoint})
        self.audit.log(provider=self.name, resource=resource, status="provider_fetch_success", cache_hit=False, data_quality="live", message="Fetched and cached OpenFIGI response.")
        return response

    def _http_post_json(self, endpoint: str, payload: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Atlas/0.6B"}
        if self.api_key:
            headers["X-OPENFIGI-APIKEY"] = self.api_key
        if self.fetch_json is not None:
            return self.fetch_json(url, headers, payload)
        body = json.dumps(payload).encode("utf-8")
        if self.fetch_json is not None:
            return self.fetch_json(url, headers, payload)
        request = Request(url, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout) as response:  # nosec - controlled URLs only
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _records_from_mapping_payload(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            return []
        records: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict) and isinstance(item.get("data"), list):
                records.extend([record for record in item["data"] if isinstance(record, dict)])
        return records

    @staticmethod
    def _records_from_search_payload(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return [record for record in payload["data"] if isinstance(record, dict)]
        return []

    def _records_to_matches(self, query: str, records: list[dict[str, Any]], *, match_type: str) -> list[IdentifierMatch]:
        matches: list[IdentifierMatch] = []
        seen: set[str] = set()
        for record in records:
            symbol = str(record.get("ticker") or record.get("securityDescription") or "").strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            security_type = str(record.get("securityType2") or record.get("securityType") or "").lower()
            asset_class = AssetClass.ETF if "fund" in security_type or "etf" in security_type else AssetClass.STOCK
            matches.append(
                IdentifierMatch(
                    query=query,
                    symbol=symbol,
                    name=str(record.get("name") or record.get("securityDescription") or symbol),
                    asset_class=asset_class,
                    match_type=match_type,
                    confidence=100 if match_type in {"symbol", "isin"} else 78,
                    exchange=record.get("exchCode"),
                    figi=record.get("figi") or record.get("compositeFIGI"),
                    provider=self.name,
                    data_quality=self._quality(DataQualityLevel.DELAYED, ["OpenFIGI normalized identifier record. ISIN/WKN enrichment may require additional source."]),
                )
            )
        return matches

    @staticmethod
    def _looks_like_isin(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", value.strip().upper()))

    @staticmethod
    def _looks_like_symbol(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Z0-9.\-]{1,8}", value.strip().upper()))

    def _quality(self, level: DataQualityLevel, issues: list[str]) -> DataQuality:
        return DataQuality(level=level, provider=self.name, as_of=utc_now(), issues=issues)
