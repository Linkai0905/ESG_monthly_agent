from __future__ import annotations

from esg_monthly_agent.skills.reasoning.company_exposure.runner import run as exposure_run


def assess_company_exposure(state: dict) -> dict:
    return exposure_run(state)
