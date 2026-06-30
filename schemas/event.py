from __future__ import annotations

from pydantic import Field

from .base import ESGDimension, StrictModel


class IndustryEvent(StrictModel):
    event_id: str
    issue_id: str
    title: str
    event_type: str
    summary: str
    industry_signal: str
    esg_dimension: ESGDimension
    evidence_ids: list[str]
    missing_evidence: list[str] = Field(default_factory=list)


class CompanyEvent(StrictModel):
    event_id: str
    issue_id: str
    company: str
    business_segment: str
    title: str
    summary: str
    esg_impact_hint: str
    esg_dimension: ESGDimension
    evidence_ids: list[str]
    missing_evidence: list[str] = Field(default_factory=list)
