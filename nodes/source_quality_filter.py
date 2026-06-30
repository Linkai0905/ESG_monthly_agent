from __future__ import annotations

from esg_monthly_agent.skills.research_execution.source_quality_filter.runner import run as source_quality_run


def source_quality_filter(state: dict) -> dict:
    return source_quality_run(state)
