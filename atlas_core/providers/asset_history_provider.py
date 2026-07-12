from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from atlas_core.enums import DataQualityLevel
from atlas_core.models import DataQuality, OhlcvBar
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.time_utils import utc_now


class CsvAssetHistoryProvider:
    """Offline OHLCV provider used as the safe fallback data source.

    It normalizes `data/samples/asset_ohlcv.csv` into OhlcvBar records. Live or
    delayed providers can be layered in front of this provider without changing
    the engines that consume normalized bars.
    """

    name = "csv_asset_sample"

    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)
        if not self.csv_path.is_absolute():
            self.csv_path = Path.cwd() / self.csv_path
        self._history_by_symbol: Dict[str, List[OhlcvBar]] | None = None
        self._last_quality_by_symbol: dict[str, DataQuality] = {}

    def _load(self) -> Dict[str, List[OhlcvBar]]:
        if self._history_by_symbol is not None:
            return self._history_by_symbol
        result: Dict[str, List[OhlcvBar]] = defaultdict(list)
        if not self.csv_path.exists():
            self._history_by_symbol = {}
            return self._history_by_symbol
        with self.csv_path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                symbol = row["symbol"].upper().strip()
                result[symbol].append(
                    OhlcvBar(
                        symbol=symbol,
                        date=row["date"],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(float(row["volume"])),
                        source=self.name,
                    )
                )
        for bars in result.values():
            bars.sort(key=lambda bar: bar.date)
        self._history_by_symbol = dict(result)
        return self._history_by_symbol

    def history_for(self, symbol: str) -> List[OhlcvBar]:
        normalized = symbol.upper().strip()
        bars = list(self._load().get(normalized, []))
        self._last_quality_by_symbol[normalized] = self.data_quality_for(normalized, bars=bars)
        return bars

    def data_quality_for(self, symbol: str, bars: Optional[List[OhlcvBar]] = None) -> DataQuality:
        normalized = symbol.upper().strip()
        if bars is None:
            bars = list(self._load().get(normalized, []))
        issues = [
            "Offline bundled OHLCV sample is active. Do not treat sample bars as live market data.",
        ]
        if not bars:
            issues.append("No OHLCV sample bars found for this symbol.")
        return DataQuality(
            level=DataQualityLevel.SAMPLE,
            provider=self.name,
            as_of=utc_now(),
            issues=issues,
        )


class YFinanceAssetHistoryProvider:
    """Controlled yfinance daily OHLCV provider with cache, audit and fallback.

    Sprint 6A activates the first real/delayed asset-level market-data path. The
    provider remains safe by design:

    - network calls are only attempted when `live_enabled=True`;
    - every result is cached in the Sprint 5 JSON cache;
    - every fetch decision is audit-logged;
    - stale cache can be used when the provider fails;
    - a CSV sample fallback keeps Atlas runnable offline.

    yfinance data may be delayed, adjusted, incomplete or unavailable. Atlas
    treats it as decision-support data, never as exchange-certified realtime data.
    """

    name = "yfinance"

    def __init__(
        self,
        *,
        fallback_provider: CsvAssetHistoryProvider | None = None,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        ttl_seconds: int | float = 86400,
        period: str = "18mo",
        interval: str = "1d",
        live_enabled: bool = False,
        stale_allowed: bool = True,
    ):
        self.fallback_provider = fallback_provider
        self.cache = cache or JsonFileCache("data/cache")
        self.audit = audit or FetchAuditLogger("data/cache/fetch_audit.jsonl")
        self.ttl_seconds = ttl_seconds
        self.period = period
        self.interval = interval
        self.live_enabled = live_enabled
        self.stale_allowed = stale_allowed
        self._last_quality_by_symbol: dict[str, DataQuality] = {}

    def history_for(self, symbol: str) -> List[OhlcvBar]:
        normalized = symbol.upper().strip()
        key = self._cache_key(normalized)
        resource = f"asset_ohlcv/{normalized}/{self.period}/{self.interval}"

        if not self.live_enabled:
            self.audit.log(
                provider=self.name,
                resource=resource,
                status="disabled_by_config_fallback",
                cache_hit=False,
                data_quality="sample",
                message="asset_data.live_providers_enabled is false; CSV sample fallback used.",
            )
            return self._fallback(normalized, ["yfinance is configured but live provider calls are disabled."])

        cached = self.cache.get("asset_ohlcv", key, ttl_seconds=self.ttl_seconds)
        if cached.hit and cached.payload:
            bars = self._bars_from_payload(cached.payload, source="yfinance_cache")
            quality = self._quality(
                level=DataQualityLevel.DELAYED,
                provider="yfinance_cache",
                issues=[
                    "OHLCV bars loaded from local yfinance cache.",
                    "yfinance data may be delayed, adjusted, incomplete or unavailable.",
                ],
            )
            self._last_quality_by_symbol[normalized] = quality
            self.audit.log(
                provider=self.name,
                resource=resource,
                status="cache_hit",
                cache_hit=True,
                data_quality="delayed",
                message=f"Loaded {len(bars)} cached OHLCV bars.",
            )
            return bars

        stale_payload = cached.payload if cached.expired and cached.payload else None
        try:
            bars = self._fetch_from_yfinance(normalized)
        except Exception as exc:  # pragma: no cover - exact provider failures vary by environment
            message = f"yfinance fetch failed: {type(exc).__name__}: {exc}"
            if stale_payload and self.stale_allowed:
                bars = self._bars_from_payload(stale_payload, source="yfinance_stale_cache")
                quality = self._quality(
                    level=DataQualityLevel.PARTIAL,
                    provider="yfinance_stale_cache",
                    issues=[
                        message,
                        "Expired yfinance cache used because live provider failed.",
                        "Manual review required before using levels for real decisions.",
                    ],
                )
                self._last_quality_by_symbol[normalized] = quality
                self.audit.log(
                    provider=self.name,
                    resource=resource,
                    status="provider_failed_stale_cache_used",
                    cache_hit=True,
                    data_quality="partial",
                    message=message,
                )
                return bars
            self.audit.log(
                provider=self.name,
                resource=resource,
                status="provider_failed_fallback",
                cache_hit=False,
                data_quality="sample",
                message=message,
            )
            return self._fallback(normalized, [message, "CSV sample fallback used after provider failure."])

        if not bars:
            self.audit.log(
                provider=self.name,
                resource=resource,
                status="empty_response_fallback",
                cache_hit=False,
                data_quality="sample",
                message="yfinance returned no valid OHLCV bars; CSV sample fallback used.",
            )
            return self._fallback(normalized, ["yfinance returned no valid OHLCV bars."])

        self.cache.set(
            "asset_ohlcv",
            key,
            [bar.model_dump(mode="json") for bar in bars],
            metadata={"provider": self.name, "symbol": normalized, "period": self.period, "interval": self.interval},
        )
        quality = self._quality(
            level=DataQualityLevel.DELAYED,
            provider=self.name,
            issues=[
                "OHLCV bars fetched through yfinance and cached locally.",
                "Data may be delayed, adjusted, incomplete or unavailable; verify externally before real-world execution.",
            ],
        )
        self._last_quality_by_symbol[normalized] = quality
        self.audit.log(
            provider=self.name,
            resource=resource,
            status="provider_fetch_success",
            cache_hit=False,
            data_quality="delayed",
            message=f"Fetched and cached {len(bars)} OHLCV bars.",
        )
        return bars

    def data_quality_for(self, symbol: str) -> DataQuality:
        normalized = symbol.upper().strip()
        return self._last_quality_by_symbol.get(
            normalized,
            self._quality(
                level=DataQualityLevel.MISSING,
                provider=self.name,
                issues=["No yfinance fetch has been attempted for this symbol in the current process."],
            ),
        )

    def _fetch_from_yfinance(self, symbol: str) -> List[OhlcvBar]:
        try:
            import yfinance as yf  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("yfinance is not available. Install requirements or use CSV provider.") from exc

        ticker = yf.Ticker(symbol)
        raw = ticker.history(period=self.period, interval=self.interval, auto_adjust=False)
        if raw is None or raw.empty:
            return []
        return self._bars_from_dataframe(symbol, raw, source=self.name)

    def _bars_from_dataframe(self, symbol: str, df: pd.DataFrame, *, source: str) -> List[OhlcvBar]:
        bars: list[OhlcvBar] = []
        for idx, row in df.iterrows():
            try:
                open_value = float(row["Open"])
                high_value = float(row["High"])
                low_value = float(row["Low"])
                close_value = float(row["Close"])
            except Exception:
                continue
            if any(pd.isna(value) or value <= 0 for value in [open_value, high_value, low_value, close_value]):
                continue
            volume_raw = row["Volume"] if "Volume" in row else 0
            volume_value = 0 if pd.isna(volume_raw) else int(float(volume_raw))
            if hasattr(idx, "date"):
                bar_date = idx.date().isoformat()
            else:
                bar_date = pd.to_datetime(idx).date().isoformat()
            bars.append(
                OhlcvBar(
                    symbol=symbol.upper(),
                    date=bar_date,
                    open=open_value,
                    high=high_value,
                    low=low_value,
                    close=close_value,
                    volume=volume_value,
                    source=source,
                )
            )
        bars.sort(key=lambda bar: bar.date)
        return bars

    @staticmethod
    def _bars_from_payload(payload: object, *, source: str) -> List[OhlcvBar]:
        bars: list[OhlcvBar] = []
        if not isinstance(payload, list):
            return bars
        for row in payload:
            if not isinstance(row, dict):
                continue
            normalized = dict(row)
            normalized["source"] = source
            try:
                bars.append(OhlcvBar(**normalized))
            except Exception:
                continue
        bars.sort(key=lambda bar: bar.date)
        return bars

    def _fallback(self, symbol: str, extra_issues: list[str]) -> List[OhlcvBar]:
        if self.fallback_provider is None:
            quality = self._quality(level=DataQualityLevel.MISSING, provider=self.name, issues=extra_issues + ["No fallback provider configured."])
            self._last_quality_by_symbol[symbol] = quality
            return []
        bars = self.fallback_provider.history_for(symbol)
        fallback_quality = self.fallback_provider.data_quality_for(symbol, bars=bars)
        quality = DataQuality(
            level=fallback_quality.level,
            provider=f"{self.name}_fallback->{fallback_quality.provider}",
            as_of=utc_now(),
            issues=extra_issues + fallback_quality.issues,
        )
        self._last_quality_by_symbol[symbol] = quality
        return bars

    def _quality(self, *, level: DataQualityLevel, provider: str, issues: list[str]) -> DataQuality:
        return DataQuality(level=level, provider=provider, as_of=utc_now(), issues=issues)

    def _cache_key(self, symbol: str) -> str:
        return f"{self.name}:{symbol}:{self.period}:{self.interval}"
