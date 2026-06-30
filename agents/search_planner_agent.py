from __future__ import annotations

from esg_monthly_agent.skills.common import plan_search_tasks
from esg_monthly_agent.schemas import dump_model


class SearchPlannerAgent:
    def invoke(self, state: dict) -> list[dict]:
        return dump_model(plan_search_tasks(state))
