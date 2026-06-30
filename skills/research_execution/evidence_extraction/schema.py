from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import EvidenceItem, StrictModel


class EvidenceExtractionInput(StrictModel):
    state: dict = Field(default_factory=dict)


class EvidenceExtractionOutput(StrictModel):
    evidence_items: list[EvidenceItem]
