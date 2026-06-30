from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import IssueChain, StrictModel


class IssueChainBuilderInput(StrictModel):
    state: dict = Field(default_factory=dict)


class IssueChainBuilderOutput(StrictModel):
    issue_chains: list[IssueChain]
