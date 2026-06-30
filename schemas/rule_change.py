from __future__ import annotations

from pydantic import Field

from .base import StrictModel


class RuleChange(StrictModel):
    rule_id: str
    issue_id: str
    title: str
    rule_type: str
    publisher: str
    publish_date: str | None = None
    summary: str
    expected_impact: str
    evidence_ids: list[str]
    source_priority: str
    missing_evidence: list[str] = Field(default_factory=list)
