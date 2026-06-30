from __future__ import annotations

from esg_monthly_agent.skills.research_execution.search_executor.runner import run as search_executor_run


def execute_issue_aware_search(state: dict) -> dict:
    return search_executor_run(state)
