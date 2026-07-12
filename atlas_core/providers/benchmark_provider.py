from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

import pandas as pd

from atlas_core.enums import DataQualityLevel
from atlas_core.models import DataQuality
from atlas_core.utils.time_utils import utc_now


class BenchmarkHistoryProvider(ABC):
    name: str

    @abstractmethod
    def get_history(self, symbols: Iterable[str], lookback_days: int = 320) -> pd.DataFrame:
        """Return OHLCV history with columns: date, symbol, open, high, low, close, volume."""
        raise NotImplementedError

    @abstractmethod
    def data_quality(self) -> DataQuality:
        raise NotImplementedError


class CSVBenchmarkProvider(BenchmarkHistoryProvider):
    """Offline benchmark provider backed by CSV data.

    This is deterministic and testable. It represents the Sprint 1 fallback data source and can be
    replaced by YFinanceBenchmarkProvider without changing MarketEngine.
    """

    name = "csv_benchmark_sample"

    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)
        if not self.csv_path.is_absolute():
            self.csv_path = Path.cwd() / self.csv_path

    def get_history(self, symbols: Iterable[str], lookback_days: int = 320) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Benchmark CSV not found: {self.csv_path}")
        df = pd.read_csv(self.csv_path, parse_dates=["date"])
        requested = {symbol.upper() for symbol in symbols}
        df["symbol"] = df["symbol"].str.upper()
        filtered = df[df["symbol"].isin(requested)].copy()
        filtered = filtered.sort_values(["symbol", "date"])
        if lookback_days > 0:
            filtered = filtered.groupby("symbol", group_keys=False).tail(lookback_days)
        return filtered.reset_index(drop=True)

    def data_quality(self) -> DataQuality:
        return DataQuality(
            level=DataQualityLevel.SAMPLE,
            provider=self.name,
            as_of=utc_now(),
            issues=[
                "Sprint 1 fallback uses bundled benchmark_history.csv. Use yfinance/live provider for current market data.",
            ],
        )


class YFinanceBenchmarkProvider(BenchmarkHistoryProvider):
    """Optional live/delayed benchmark provider.

    yfinance is imported lazily so Sprint 1 remains runnable in offline environments and tests.
    """

    name = "yfinance"

    def __init__(self, period: str = "18mo", interval: str = "1d"):
        self.period = period
        self.interval = interval
        self._last_issues: list[str] = []

    def get_history(self, symbols: Iterable[str], lookback_days: int = 320) -> pd.DataFrame:
        try:
            import yfinance as yf  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError("yfinance is not installed. Install requirements or use CSV provider.") from exc

        frames: list[pd.DataFrame] = []
        self._last_issues = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            raw = ticker.history(period=self.period, interval=self.interval, auto_adjust=False)
            if raw.empty:
                self._last_issues.append(f"No yfinance history returned for {symbol}.")
                continue
            raw = raw.reset_index()
            date_col = "Date" if "Date" in raw.columns else raw.columns[0]
            frame = pd.DataFrame(
                {
                    "date": pd.to_datetime(raw[date_col]).dt.tz_localize(None),
                    "symbol": symbol.upper(),
                    "open": raw["Open"].astype(float),
                    "high": raw["High"].astype(float),
                    "low": raw["Low"].astype(float),
                    "close": raw["Close"].astype(float),
                    "volume": raw.get("Volume", pd.Series([0] * len(raw))).astype(float),
                }
            )
            frames.append(frame.tail(lookback_days))
        if not frames:
            raise RuntimeError("No benchmark history could be loaded from yfinance.")
        return pd.concat(frames, ignore_index=True).sort_values(["symbol", "date"])

    def data_quality(self) -> DataQuality:
        return DataQuality(
            level=DataQualityLevel.DELAYED,
            provider=self.name,
            as_of=utc_now(),
            issues=self._last_issues + ["yfinance data may be delayed, adjusted, incomplete, or unavailable."],
        )
