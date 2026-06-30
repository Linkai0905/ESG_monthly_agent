from __future__ import annotations

from pydantic import Field

from .base import StrictModel


class Recommendation(StrictModel):
    recommendation_id: str
    issue_id: str
    company: str
    recommendation: str
    rationale: str
    expected_esg_value: str
    action_owner: list[str]
    suggested_kpis: list[str]
    time_horizon: str
    evidence_ids: list[str]
    related_rule_ids: list[str]
    related_industry_event_ids: list[str]
    related_company_event_ids: list[str]
    related_peer_action_ids: list[str]
    priority: str
    confidence: float = Field(ge=0, le=1)
