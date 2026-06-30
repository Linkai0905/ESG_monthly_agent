from __future__ import annotations

from typing import Protocol

from esg_monthly_agent.schemas.deepsearch import DeepSearchResult, DeepSearchTask


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderRuntimeError(RuntimeError):
    pass


class DeepSearchProvider(Protocol):
    name: str

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        ...
