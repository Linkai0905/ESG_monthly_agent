from __future__ import annotations

from pydantic import Field

from .base import StrictModel


class CompanyProfile(StrictModel):
    company: str
    aliases: list[str] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    industry: list[str] = Field(default_factory=list)
    business_segments: list[str] = Field(default_factory=list)
    peers: list[str] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class CustomerSegment(StrictModel):
    segment_id: str
    segment_name: str
    description: str
    revenue_driver: str
    geography: list[str] = Field(default_factory=list)
    esg_touchpoints: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
