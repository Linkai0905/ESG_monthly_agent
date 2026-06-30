from __future__ import annotations

from esg_monthly_agent.skills.reasoning.issue_chain_builder.runner import run as issue_chain_run


def build_issue_chains(state: dict) -> dict:
    return issue_chain_run(state)
