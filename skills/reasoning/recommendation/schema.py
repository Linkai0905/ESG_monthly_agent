from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import Recommendation, StrictModel


class RecommendationInput(StrictModel):
    state: dict = Field(default_factory=dict)


class RecommendationOutput(StrictModel):
    recommendations: list[Recommendation]
