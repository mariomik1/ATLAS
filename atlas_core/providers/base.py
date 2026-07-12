from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field

from atlas_core.models import Asset, ChartContext, DataQuality, FundamentalContext, IdentifierMatch, OhlcvBar


class AssetMarketData(BaseModel):
    asset: Asset
    current_price: float = Field(gt=0)
    atr_pct: float = Field(gt=0)
    momentum_hint: float = Field(default=70, ge=0, le=100)
    fundamental_hint: float = Field(default=70, ge=0, le=100)
    data_quality: DataQuality
    history: List[OhlcvBar] = Field(default_factory=list)
    chart_context: Optional[ChartContext] = None
    fundamental_context: Optional[FundamentalContext] = None
    identifier_match: Optional[IdentifierMatch] = None


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    def get_watchlist_market_data(self) -> List[AssetMarketData]:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, query: str) -> Optional[AssetMarketData]:
        raise NotImplementedError
