from __future__ import annotations

from pydantic import Field

from .base import ESGDimension, StrictModel


class MaterialityTopic(StrictModel):
    issue_id: str
    issue_name: str
    description: str
    esg_dimensions: list[ESGDimension]
    materiality_level: str
    related_segments: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class IssueChain(StrictModel):
    issue_id: str
    issue_name: str
    rule_change_ids: list[str]
    industry_event_ids: list[str]
    company_event_ids: list[str]
    peer_action_ids: list[str]
    chain_summary: str
    logic_path: str
    missing_links: list[str]
    confidence: float = Field(ge=0, le=1)
