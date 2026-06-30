from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import QualityCheckResult, StrictModel


class QualityReviewInput(StrictModel):
    state: dict = Field(default_factory=dict)


class QualityReviewOutput(StrictModel):
    quality_checks: QualityCheckResult
    needs_repair: bool
