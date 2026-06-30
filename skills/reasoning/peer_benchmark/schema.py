from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import StrictModel


class PeerBenchmarkInput(StrictModel):
    state: dict = Field(default_factory=dict)


class PeerBenchmarkOutput(StrictModel):
    warnings: list[dict] = Field(default_factory=list)
