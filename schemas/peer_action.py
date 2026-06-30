from __future__ import annotations

from pydantic import Field

from .base import ESGDimension, StrictModel


class PeerAction(StrictModel):
    peer_action_id: str
    issue_id: str
    peer_company: str
    action: str
    action_type: str
    benchmark_value: str
    esg_dimension: ESGDimension
    evidence_ids: list[str]
    missing_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
