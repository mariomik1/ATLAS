from __future__ import annotations

from atlas_core.providers.status import ProviderRegistry, ProviderStatus


class LiveProviderDisabled(RuntimeError):
    pass


class ActivatedProviderStub:
    """Safety wrapper for future API providers.

    Sprint 5 prepares activation, status, cache and audit plumbing but does not
    implement production API fetches. Real adapters must subclass or replace this
    wrapper and map payloads into Atlas models before engines consume the data.
    """

    def __init__(self, role: str, registry: ProviderRegistry):
        self.role = role
        self.registry = registry
        self.status: ProviderStatus = registry.status_for(role)

    def assert_can_fetch(self) -> None:
        if self.status.status != "ready_for_live_fetch" and self.status.status != "network_optional_ready":
            self.registry.log_provider_decision(self.status)
            raise LiveProviderDisabled(
                f"Provider {self.status.selected_provider} for {self.role} is not enabled: {self.status.status}"
            )
