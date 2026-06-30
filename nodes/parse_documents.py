from __future__ import annotations

from esg_monthly_agent.skills.research_execution.fetch_and_parse.runner import parse


def parse_documents(state: dict) -> dict:
    return parse(state)
