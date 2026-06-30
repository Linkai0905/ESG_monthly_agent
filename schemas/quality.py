from __future__ import annotations

from pydantic import Field

from .base import StrictModel


class QualityCheckResult(StrictModel):
    passed: bool
    repairable: bool
    missing_links: list[str] = Field(default_factory=list)
    weak_recommendations: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    low_authority_sources: list[str] = Field(default_factory=list)
    sample_sources: list[str] = Field(default_factory=list)
    stale_sources: list[str] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
