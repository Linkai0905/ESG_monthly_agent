from __future__ import annotations

from esg_monthly_agent.skills.common import write_report


def run(state: dict) -> dict:
    return write_report(state)
