from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import build_report_contract


def run(state: dict) -> dict:
    return {"report_contract": dump_model(build_report_contract(state))}
