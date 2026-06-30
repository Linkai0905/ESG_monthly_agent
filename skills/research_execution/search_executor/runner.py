from __future__ import annotations

from esg_monthly_agent.skills.common import execute_search_tasks


def run(state: dict) -> dict:
    return execute_search_tasks(state)
