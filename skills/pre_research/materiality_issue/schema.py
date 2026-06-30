from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import MaterialityTopic, StrictModel


class MaterialityIssueInput(StrictModel):
    state: dict = Field(default_factory=dict)


class MaterialityIssueOutput(StrictModel):
    materiality_topics: list[MaterialityTopic]
