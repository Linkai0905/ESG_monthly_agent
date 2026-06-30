from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import plan_search_tasks


def run(state: dict) -> dict:
    return {"search_tasks": dump_model(plan_search_tasks(state))}
