from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import ReportContract, StrictModel


class ReportContractInput(StrictModel):
    state: dict = Field(default_factory=dict)


class ReportContractOutput(StrictModel):
    report_contract: ReportContract
