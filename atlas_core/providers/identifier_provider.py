from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import DataQuality, IdentifierMatch, SearchResult
from atlas_core.utils.time_utils import utc_now


class CsvIdentifierProvider:
    """Offline security master for ticker/name/ISIN/WKN-style search."""

    name = "csv_identifier_master"

    def __init__(self, csv_path: str | Path = "data/samples/identifier_master.csv"):
        self.csv_path = Path(csv_path)
        self.rows = self._load_rows()
        self.matches = [self._row_to_match(row, query=row.get("symbol", ""), match_type="symbol") for row in self.rows]
        self.index = self._build_index(self.rows)

    def resolve(self, query: str) -> Optional[IdentifierMatch]:
        normalized = self._normalize(query)
        row = self.index.get(normalized)
        if row is None:
            return None
        return self._row_to_match(row, query=query, match_type=self._match_type(row, normalized))

    def search(self, query: str, limit: int = 10) -> SearchResult:
        normalized = self._normalize(query)
        matches: list[IdentifierMatch] = []
        seen: set[str] = set()
        exact_row = self.index.get(normalized)
        if exact_row:
            exact = self._row_to_match(exact_row, query=query, match_type=self._match_type(exact_row, normalized), confidence=100)
            matches.append(exact)
            seen.add(exact.symbol)
        for row in self.rows:
            symbol = row.get("symbol", "").upper()
            haystack = " ".join(
                [
                    row.get("symbol", ""),
                    row.get("name", ""),
                    row.get("sector", ""),
                    row.get("industry", ""),
                    row.get("isin", ""),
                    row.get("wkn", ""),
                    row.get("aliases", ""),
                ]
            ).lower()
            if normalized and normalized in haystack and symbol not in seen:
                matches.append(self._row_to_match(row, query=query, match_type="partial", confidence=75))
                seen.add(symbol)
            if len(matches) >= limit:
                break
        return SearchResult(
            query=query,
            matches=matches,
            data_quality=DataQuality(
                level=DataQualityLevel.SAMPLE,
                provider=self.name,
                as_of=utc_now(),
                issues=["Sprint 4 uses sample identifier master. Validate WKN/ISIN mapping before real decisions."],
            ),
        )

    def metadata_for_symbol(self, symbol: str) -> dict[str, str]:
        normalized = symbol.strip().upper()
        for row in self.rows:
            if row.get("symbol", "").upper() == normalized:
                return row
        return {}

    def _load_rows(self) -> list[dict[str, str]]:
        if not self.csv_path.exists():
            return []
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    def _build_index(self, rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
        index: dict[str, dict[str, str]] = {}
        for row in rows:
            aliases = [alias.strip() for alias in (row.get("aliases") or "").split("|") if alias.strip()]
            keys = [row.get("symbol"), row.get("name"), row.get("isin"), row.get("wkn")] + aliases
            for key in keys:
                if key:
                    index[self._normalize(key)] = row
        return index

    def _row_to_match(self, row: dict[str, str], *, query: str, match_type: str, confidence: float = 100) -> IdentifierMatch:
        return IdentifierMatch(
            query=query,
            symbol=row.get("symbol", "").strip().upper(),
            name=row.get("name") or row.get("symbol", "").strip().upper(),
            asset_class=AssetClass(row.get("asset_class", "stock") or "stock"),
            match_type=match_type,
            confidence=confidence,
            exchange=self._clean(row.get("exchange")),
            country=self._clean(row.get("country")),
            currency=row.get("currency") or "USD",
            isin=self._clean(row.get("isin")),
            wkn=self._clean(row.get("wkn")),
            provider=self.name,
            data_quality=DataQuality(
                level=DataQualityLevel(row.get("data_quality", "sample") or "sample"),
                provider=self.name,
                as_of=utc_now(),
                issues=["Sample identifier record; validate identifier against live provider before execution."],
            ),
        )

    def _match_type(self, row: dict[str, str], normalized: str) -> str:
        if normalized == self._normalize(row.get("symbol")):
            return "symbol"
        if normalized == self._normalize(row.get("isin")):
            return "isin"
        if normalized == self._normalize(row.get("wkn")):
            return "wkn"
        if normalized == self._normalize(row.get("name")):
            return "name"
        aliases = [self._normalize(alias) for alias in (row.get("aliases") or "").split("|")]
        if normalized in aliases:
            return "alias"
        return "partial"

    @staticmethod
    def _normalize(value: str | None) -> str:
        return (value or "").strip().lower()

    @staticmethod
    def _clean(value: str | None) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None
