from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import CompanyEvent, IndustryEvent, PeerAction, RuleChange, StrictModel


class EventClassificationInput(StrictModel):
    state: dict = Field(default_factory=dict)


class EventClassificationOutput(StrictModel):
    rule_changes: list[RuleChange] = Field(default_factory=list)
    industry_events: list[IndustryEvent] = Field(default_factory=list)
    company_events: list[CompanyEvent] = Field(default_factory=list)
    peer_actions: list[PeerAction] = Field(default_factory=list)
