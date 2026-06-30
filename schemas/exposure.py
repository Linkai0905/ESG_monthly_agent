from __future__ import annotations

from pydantic import Field

from .base import ESGDimension, StrictModel


class CompanyExposure(StrictModel):
    exposure_id: str
    issue_id: str
    company: str
    affected_segments: list[str]
    esg_dimension: ESGDimension
    risk_level: str
    opportunity_level: str
    rationale: str
    evidence_ids: list[str]
    missing_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
