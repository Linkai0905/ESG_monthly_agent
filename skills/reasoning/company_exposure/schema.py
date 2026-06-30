from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import CompanyExposure, StrictModel


class CompanyExposureInput(StrictModel):
    state: dict = Field(default_factory=dict)


class CompanyExposureOutput(StrictModel):
    company_exposures: list[CompanyExposure]
