from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import SearchTask, StrictModel


class SearchTaskPlannerInput(StrictModel):
    state: dict = Field(default_factory=dict)


class SearchTaskPlannerOutput(StrictModel):
    search_tasks: list[SearchTask]
