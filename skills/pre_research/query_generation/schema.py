from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import StrictModel


class QueryGenerationInput(StrictModel):
    state: dict = Field(default_factory=dict)


class QueryGenerationOutput(StrictModel):
    generated_queries: list[dict]
