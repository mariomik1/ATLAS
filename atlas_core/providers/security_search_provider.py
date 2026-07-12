from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import pandas as pd

from atlas_core.config_loader import PROJECT_ROOT
from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import DataQuality, IdentifierMatch, SearchResult
from atlas_core.utils.time_utils import utc_now


class SecuritySearchProvider(ABC):
    name: str

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> SearchResult:
        raise NotImplementedError


class CsvSecuritySearchProvider(SecuritySearchProvider):
    """Offline search provider for ticker, name, ISIN, WKN and aliases."""

    name = "csv_sample_security_search"

    def __init__(self, settings: dict):
        cfg = settings.get("identifier_search", {})
        self.csv_path = self._project_path(cfg.get("csv_path", "data/samples/security_master.csv"))
        self.quality = DataQuality(
            level=DataQualityLevel(cfg.get("data_quality_level", "sample")),
            provider=self.name,
            as_of=utc_now(),
            issues=["Sprint 4 uses deterministic sample security master data. Not live identifier mapping."],
        )
        self._records = self._load_records()

    @staticmethod
    def _project_path(value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    def _load_records(self) -> list[dict]:
        if not self.csv_path.exists():
            return []
        df = pd.read_csv(self.csv_path)
        records = []
        for _, row in df.iterrows():
            payload = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            payload["aliases"] = self._split_aliases(payload.get("aliases"))
            records.append(payload)
        return records

    @staticmethod
    def _split_aliases(value) -> list[str]:
        if value is None:
            return []
        return [part.strip() for part in str(value).split("|") if part.strip()]

    def search(self, query: str, limit: int = 10) -> SearchResult:
        normalized = query.strip().lower()
        if not normalized:
            return SearchResult(query=query, matches=[], data_quality=self.quality)
        matches: list[IdentifierMatch] = []
        for row in self._records:
            match_type, confidence = self._match(row, normalized)
            if confidence <= 0:
                continue
            matches.append(
                IdentifierMatch(
                    query=query,
                    symbol=str(row["symbol"]).upper(),
                    name=str(row.get("name") or row["symbol"]),
                    asset_class=AssetClass(str(row.get("asset_class") or "stock")),
                    match_type=match_type,
                    confidence=confidence,
                    exchange=row.get("exchange"),
                    country=row.get("country"),
                    currency=str(row.get("currency") or "USD"),
                    isin=row.get("isin"),
                    wkn=row.get("wkn"),
                    figi=row.get("figi"),
                    provider=self.name,
                    data_quality=self.quality,
                )
            )
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return SearchResult(query=query, matches=matches[:limit], data_quality=self.quality)

    @staticmethod
    def _match(row: dict, query: str) -> tuple[str, float]:
        symbol = str(row.get("symbol") or "").lower()
        name = str(row.get("name") or "").lower()
        isin = str(row.get("isin") or "").lower()
        wkn = str(row.get("wkn") or "").lower()
        aliases = [str(alias).lower() for alias in row.get("aliases", [])]
        if query == symbol:
            return "ticker", 100
        if query == isin and isin:
            return "isin", 100
        if query == wkn and wkn:
            return "wkn", 100
        if query == name:
            return "name", 96
        if query in aliases:
            return "alias", 92
        if query and query in name:
            return "partial_name", 75
        if any(query in alias for alias in aliases):
            return "partial_alias", 70
        if symbol.startswith(query):
            return "partial_ticker", 65
        return "none", 0


class FutureLiveSecuritySearchProvider(SecuritySearchProvider):
    """Placeholder for FMP/OpenFIGI security search adapters."""

    name = "future_live_security_search"

    def search(self, query: str, limit: int = 10) -> SearchResult:
        raise NotImplementedError("Live identifier providers are intentionally disabled in Sprint 4.")
