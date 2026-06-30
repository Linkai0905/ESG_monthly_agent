from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import EvidenceNeed, StrictModel


class EvidenceNeedBuilderInput(StrictModel):
    state: dict = Field(default_factory=dict)


class EvidenceNeedBuilderOutput(StrictModel):
    evidence_needs: list[EvidenceNeed]
