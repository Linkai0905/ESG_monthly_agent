from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import StrictModel


class SourceRegistryInput(StrictModel):
    state: dict = Field(default_factory=dict)


class SourceRegistryOutput(StrictModel):
    source_registry: list[dict]
