from __future__ import annotations

from esg_monthly_agent.skills.common import generate_issue_queries


def run(state: dict) -> dict:
    return {"generated_queries": generate_issue_queries(state)}
