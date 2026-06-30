from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import build_issue_chains


def run(state: dict) -> dict:
    return {"issue_chains": dump_model(build_issue_chains(state))}
