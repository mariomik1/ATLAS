from __future__ import annotations

from typing import Optional

from atlas_core.models import SearchResult
from atlas_core.providers.base import AssetMarketData
from atlas_core.providers.manual_provider import ManualSampleProvider


class IdentifierResolver:
    """Resolve ticker, name, ISIN or WKN to an asset using provider search.

    Sprint 4 delegates identifier matching to the provider's search master, which
    can later be backed by OpenFIGI/FMP without changing downstream engines.
    """

    def __init__(self, provider: ManualSampleProvider):
        self.provider = provider

    def resolve(self, query: str) -> Optional[AssetMarketData]:
        return self.provider.resolve(query)

    def search(self, query: str, limit: int = 10) -> SearchResult:
        return self.provider.search(query, limit=limit)
