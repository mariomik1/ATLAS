from __future__ import annotations

import re
from typing import Any, Optional

from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import DataQuality, IdentifierMatch, SearchResult
from atlas_core.providers.fmp_client import FmpClient
from atlas_core.providers.identifier_provider import CsvIdentifierProvider
from atlas_core.utils.time_utils import utc_now


class FmpIdentifierProvider:
    """FMP-backed ticker/name/ISIN search with sample fallback.

    FMP is used only when explicitly enabled and a key is present. Otherwise the
    local identifier master remains the source of truth for offline operation.
    """

    name = "fmp_identifiers"

    def __init__(
        self,
        *,
        client: FmpClient,
        fallback_provider: CsvIdentifierProvider | None = None,
        live_enabled: bool = False,
    ):
        self.client = client
        self.fallback_provider = fallback_provider or CsvIdentifierProvider()
        self.live_enabled = live_enabled

    def resolve(self, query: str) -> Optional[IdentifierMatch]:
        result = self.search(query, limit=1)
        return result.matches[0] if result.matches else None

    def search(self, query: str, limit: int = 10) -> SearchResult:
        cleaned = query.strip()
        if not cleaned:
            return SearchResult(query=query, matches=[], data_quality=self._quality(DataQualityLevel.MISSING, ["Empty search query."]))
        if not self.live_enabled or not self.client.ready:
            fallback = self.fallback_provider.search(query, limit=limit)
            fallback.data_quality.provider = f"{fallback.data_quality.provider}+fmp_disabled_fallback"
            fallback.data_quality.issues.append("FMP identifier provider is disabled or FMP_API_KEY is missing.")
            return fallback
        try:
            matches = self._live_search(cleaned, limit=limit)
        except Exception as exc:
            fallback = self.fallback_provider.search(query, limit=limit)
            fallback.data_quality.provider = f"{fallback.data_quality.provider}+fmp_failed_fallback"
            fallback.data_quality.level = DataQualityLevel.PARTIAL
            fallback.data_quality.issues.append(f"FMP identifier search failed: {type(exc).__name__}: {exc}")
            return fallback
        if not matches:
            return SearchResult(
                query=query,
                matches=[],
                data_quality=self._quality(DataQualityLevel.MISSING, ["FMP returned no identifier matches."]),
            )
        return SearchResult(
            query=query,
            matches=matches[:limit],
            data_quality=self._quality(
                DataQualityLevel.LIVE,
                ["FMP identifier search used. Validate exchange/ISIN before execution."],
            ),
        )

    def _live_search(self, query: str, limit: int) -> list[IdentifierMatch]:
        payloads: list[Any] = []
        if self._looks_like_isin(query):
            payloads.append(self.client.get_json("search-isin", {"isin": query.upper()}, namespace="identifiers", resource=f"fmp/search-isin/{query.upper()}"))
        else:
            payloads.append(self.client.get_json("search-name", {"query": query}, namespace="identifiers", resource=f"fmp/search-name/{query}"))
            if self._looks_like_symbol(query):
                payloads.append(self.client.get_json("search-symbol", {"query": query.upper()}, namespace="identifiers", resource=f"fmp/search-symbol/{query.upper()}"))
        records: list[dict[str, Any]] = []
        for payload in payloads:
            records.extend(self._records_from_payload(payload))
        return self._records_to_matches(query, records, limit=limit)

    @staticmethod
    def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("data", "results", "symbols"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return [payload]
        return []

    def _records_to_matches(self, query: str, records: list[dict[str, Any]], *, limit: int) -> list[IdentifierMatch]:
        matches: list[IdentifierMatch] = []
        seen: set[str] = set()
        for record in records:
            symbol = self._first(record, "symbol", "ticker")
            if not symbol:
                continue
            normalized_symbol = str(symbol).strip().upper()
            if normalized_symbol in seen:
                continue
            seen.add(normalized_symbol)
            name = self._first(record, "name", "companyName", "company_name", default=normalized_symbol)
            isin = self._first(record, "isin", "ISIN")
            asset_class = self._asset_class(record)
            match_type = self._match_type(query, normalized_symbol, str(name or ""), isin)
            confidence = self._confidence(match_type)
            matches.append(
                IdentifierMatch(
                    query=query,
                    symbol=normalized_symbol,
                    name=str(name or normalized_symbol),
                    asset_class=asset_class,
                    match_type=match_type,
                    confidence=confidence,
                    exchange=self._first(record, "exchangeShortName", "exchange", "stockExchange"),
                    country=self._first(record, "country"),
                    currency=str(self._first(record, "currency", default="USD") or "USD"),
                    isin=isin,
                    provider=self.name,
                    data_quality=self._quality(
                        DataQualityLevel.LIVE,
                        ["Identifier match from FMP. WKN is not provided by FMP and may require local/OpenFIGI enrichment."],
                    ),
                )
            )
        matches.sort(key=lambda match: match.confidence, reverse=True)
        return matches[:limit]

    @staticmethod
    def _first(record: dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            value = record.get(key)
            if value is not None and str(value).strip() != "":
                return value
        return default

    @staticmethod
    def _looks_like_isin(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", value.strip().upper()))

    @staticmethod
    def _looks_like_symbol(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Z0-9.\-]{1,8}", value.strip().upper()))

    @staticmethod
    def _asset_class(record: dict[str, Any]) -> AssetClass:
        raw = " ".join(str(record.get(key, "")) for key in ("type", "assetClass", "name", "companyName")).lower()
        if "etf" in raw or "fund" in raw:
            return AssetClass.ETF
        return AssetClass.STOCK

    def _match_type(self, query: str, symbol: str, name: str, isin: Any) -> str:
        q = query.strip().lower()
        if q == symbol.lower():
            return "symbol"
        if isin and q == str(isin).lower():
            return "isin"
        if q == name.lower():
            return "name"
        if q in name.lower():
            return "partial_name"
        return "provider"

    @staticmethod
    def _confidence(match_type: str) -> float:
        return {
            "symbol": 100,
            "isin": 100,
            "name": 96,
            "partial_name": 82,
            "provider": 72,
        }.get(match_type, 70)

    def _quality(self, level: DataQualityLevel, issues: list[str]) -> DataQuality:
        return DataQuality(level=level, provider=self.name, as_of=utc_now(), issues=issues)
