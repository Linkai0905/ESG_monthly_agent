from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import assess_company_exposure


def run(state: dict) -> dict:
    return {"company_exposures": dump_model(assess_company_exposure(state))}
