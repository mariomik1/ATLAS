from __future__ import annotations

from atlas_core.engines.catalyst_engine import CatalystEngine


class NewsCatalystEngine(CatalystEngine):
    """Backward-compatible alias retained after Sprint 3 naming cleanup."""

    def __init__(self, provider=None, settings: dict | None = None):
        super().__init__(settings)
        self.provider = provider

    def analyze_symbol(self, symbol: str):
        if self.provider is None:
            return self.build(symbol, [])
        return self.build(symbol, self.provider.get_news_for_symbol(symbol))

    def analyze_market(self):
        if self.provider is None:
            return self.build("MARKET", [])
        return self.build("MARKET", self.provider.get_market_news())
