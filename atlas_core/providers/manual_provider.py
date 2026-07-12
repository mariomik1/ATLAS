from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from atlas_core.enums import AssetClass, DataQualityLevel
from atlas_core.models import Asset, DataQuality, IdentifierMatch
from atlas_core.providers.asset_history_provider import CsvAssetHistoryProvider, YFinanceAssetHistoryProvider
from atlas_core.providers.base import AssetMarketData, MarketDataProvider
from atlas_core.providers.fmp_provider import FMPFundamentalsProvider, FMPIdentifierProvider
from atlas_core.providers.fundamentals_provider import CsvSampleFundamentalsProvider
from atlas_core.providers.identifier_provider import CsvIdentifierProvider
from atlas_core.providers.openfigi_provider import OpenFigiIdentifierProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.env_loader import get_secret, load_env_file
from atlas_core.utils.time_utils import utc_now


class ManualSampleProvider(MarketDataProvider):
    """Atlas asset provider with safe live-provider composition.

    Despite the historical class name, this provider is now the composition root
    for Sprint 6B. It can use offline sample data or gated live/delayed providers
    for OHLCV, fundamentals and identifiers while keeping CSV fallbacks.
    """

    name = "atlas_composite_provider"

    def __init__(self, watchlists_config: dict, history_csv_path: str | None = None, settings: dict | None = None):
        self.watchlists_config = watchlists_config
        self.settings = settings or {}
        self.identifier_map = {str(k).lower(): str(v) for k, v in watchlists_config.get("identifier_map", {}).items()}
        self.env_values = load_env_file()
        self.cache = JsonFileCache(self.settings.get("cache", {}).get("base_dir", "data/cache"))
        self.audit = FetchAuditLogger(self.settings.get("audit", {}).get("fetch_log_path", "data/cache/fetch_audit.jsonl"))
        csv_path = history_csv_path or self.settings.get("asset_data", {}).get("csv_path", "data/samples/asset_ohlcv.csv")
        self.csv_history_provider = CsvAssetHistoryProvider(Path(csv_path))
        self.history_provider = self._build_history_provider()
        self.fundamentals_provider = self._build_fundamentals_provider()
        self.identifier_provider = self._build_identifier_provider()
        self.assets = self._load_assets()

    def _ttl_seconds(self, cfg: dict, *, default: int) -> int:
        if "cache_ttl_minutes" in cfg:
            return int(float(cfg["cache_ttl_minutes"]) * 60)
        if "cache_ttl_hours" in cfg:
            return int(float(cfg["cache_ttl_hours"]) * 3600)
        if "cache_ttl_days" in cfg:
            return int(float(cfg["cache_ttl_days"]) * 86400)
        return default

    def _live_enabled(self, cfg: dict) -> bool:
        return bool(cfg.get("live_providers_enabled", self.settings.get("provider_activation", {}).get("live_providers_enabled", False)))

    def _build_history_provider(self):
        asset_cfg = self.settings.get("asset_data", {})
        provider_name = str(asset_cfg.get("provider", "csv_sample")).lower()
        if provider_name == "yfinance":
            return YFinanceAssetHistoryProvider(
                fallback_provider=self.csv_history_provider,
                cache=self.cache,
                audit=self.audit,
                ttl_seconds=self._ttl_seconds(asset_cfg, default=86400),
                period=str(asset_cfg.get("yfinance_period", "18mo")),
                interval=str(asset_cfg.get("yfinance_interval", "1d")),
                live_enabled=self._live_enabled(asset_cfg),
                stale_allowed=bool(self.settings.get("cache", {}).get("stale_allowed_when_provider_fails", True)),
            )
        return self.csv_history_provider

    def _build_fundamentals_provider(self):
        cfg = self.settings.get("fundamentals", {})
        provider_name = str(cfg.get("provider", "csv_sample")).lower()
        fallback = CsvSampleFundamentalsProvider(cfg.get("csv_path", "data/samples/fundamentals.csv"))
        if provider_name == "fmp":
            return FMPFundamentalsProvider(
                api_key=get_secret("FMP_API_KEY", self.env_values),
                live_enabled=self._live_enabled(cfg),
                fallback_provider=fallback,
                cache=self.cache,
                audit=self.audit,
                ttl_seconds=self._ttl_seconds(cfg, default=604800),
            )
        return fallback

    def _build_identifier_provider(self):
        cfg = self.settings.get("identifiers", {})
        provider_name = str(cfg.get("provider", "local_sample")).lower()
        fallback = CsvIdentifierProvider()
        common = dict(
            live_enabled=self._live_enabled(cfg),
            fallback_provider=fallback,
            cache=self.cache,
            audit=self.audit,
            ttl_seconds=self._ttl_seconds(cfg, default=2592000),
        )
        if provider_name == "fmp":
            return FMPIdentifierProvider(api_key=get_secret("FMP_API_KEY", self.env_values), **common)
        if provider_name == "openfigi":
            return OpenFigiIdentifierProvider(api_key=get_secret("OPENFIGI_API_KEY", self.env_values), **common)
        return fallback

    def _history_quality(self, symbol: str) -> DataQuality:
        if hasattr(self.history_provider, "data_quality_for"):
            return self.history_provider.data_quality_for(symbol)
        return DataQuality(
            level=DataQualityLevel.MISSING,
            provider="unknown_history_provider",
            as_of=utc_now(),
            issues=["History provider does not expose data-quality metadata."],
        )

    def _load_assets(self) -> List[AssetMarketData]:
        items = []
        for row in self.watchlists_config.get("default_watchlist", []):
            symbol = row["ticker"].upper()
            history = self.history_provider.history_for(symbol)
            quality = self._history_quality(symbol)
            if not history:
                quality.issues.append("No OHLCV history found; falling back to configured static price.")
            fundamental_context = self.fundamentals_provider.get_context(symbol)
            sector = row.get("sector") or (fundamental_context.profile.sector if fundamental_context and fundamental_context.profile else None)
            asset = Asset(
                symbol=symbol,
                name=row["name"],
                asset_class=AssetClass(row.get("asset_class", "stock")),
                sector=sector,
                theme=row.get("theme"),
                currency=row.get("currency", "USD"),
                isin=str(row.get("isin")) if row.get("isin") is not None else None,
                wkn=str(row.get("wkn")) if row.get("wkn") is not None else None,
            )
            current_price = float(history[-1].close) if history else float(row.get("sample_price", 100.0))
            items.append(
                AssetMarketData(
                    asset=asset,
                    current_price=current_price,
                    atr_pct=float(row.get("atr_pct", 3.0)),
                    momentum_hint=self._momentum_hint(symbol),
                    fundamental_hint=fundamental_context.overall_score if fundamental_context else 65,
                    data_quality=quality,
                    history=history,
                    fundamental_context=fundamental_context,
                )
            )
        return items

    @staticmethod
    def _momentum_hint(symbol: str) -> float:
        return {"MSFT": 82, "NVDA": 90, "V": 76, "CRWD": 84, "XLE": 68}.get(symbol.upper(), 65)

    def get_watchlist_market_data(self) -> List[AssetMarketData]:
        return list(self.assets)

    def resolve(self, query: str) -> Optional[AssetMarketData]:
        normalized = query.strip().lower()
        mapped = self.identifier_map.get(normalized, query).upper()
        for item in self.assets:
            if item.asset.symbol.upper() == mapped:
                return item
            if item.asset.name.lower() == normalized:
                return item
            if item.asset.isin and item.asset.isin.lower() == normalized:
                return item
            if item.asset.wkn and item.asset.wkn.lower() == normalized:
                return item
        match = self.identifier_provider.resolve(query)
        if match is None:
            return None
        return self._asset_market_data_from_identifier(match)

    def search(self, query: str, limit: int = 10):
        return self.identifier_provider.search(query, limit=limit)

    def _asset_market_data_from_identifier(self, match: IdentifierMatch) -> AssetMarketData:
        history = self.history_provider.history_for(match.symbol)
        metadata = self.identifier_provider.metadata_for_symbol(match.symbol) if hasattr(self.identifier_provider, "metadata_for_symbol") else {}
        history_quality = self._history_quality(match.symbol)
        issues = list(match.data_quality.issues) + list(history_quality.issues)
        if not history:
            issues.append("No OHLCV history found for this security; chart engine will use fallback levels.")
        quality = DataQuality(
            level=history_quality.level,
            provider=f"{match.data_quality.provider}+{history_quality.provider}",
            as_of=utc_now(),
            issues=issues,
        )
        fundamental_context = self.fundamentals_provider.get_context(match.symbol)
        sector = metadata.get("sector") or (fundamental_context.profile.sector if fundamental_context and fundamental_context.profile else None)
        asset = Asset(
            symbol=match.symbol,
            name=match.name,
            asset_class=match.asset_class,
            sector=sector,
            theme=metadata.get("theme") or None,
            currency=match.currency,
            isin=match.isin,
            wkn=match.wkn,
        )
        current_price = float(history[-1].close) if history else float(metadata.get("sample_price") or 100.0)
        atr_pct = float(metadata.get("atr_pct") or 3.0)
        momentum_hint = float(metadata.get("momentum_hint") or 65.0)
        return AssetMarketData(
            asset=asset,
            current_price=current_price,
            atr_pct=atr_pct,
            momentum_hint=momentum_hint,
            fundamental_hint=fundamental_context.overall_score if fundamental_context else 65,
            data_quality=quality,
            history=history,
            fundamental_context=fundamental_context,
            identifier_match=match,
        )
