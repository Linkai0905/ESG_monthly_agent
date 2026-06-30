from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import CompanyProfile, StrictModel


class CompanyBoundaryInput(StrictModel):
    state: dict = Field(default_factory=dict)


class CompanyBoundaryOutput(StrictModel):
    company_profile: CompanyProfile
