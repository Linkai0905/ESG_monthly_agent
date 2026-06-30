from __future__ import annotations

from esg_monthly_agent.skills.research_execution.fetch_and_parse.runner import fetch


def fetch_pages(state: dict) -> dict:
    return fetch(state)
