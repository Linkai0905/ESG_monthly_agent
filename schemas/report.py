from __future__ import annotations

from pydantic import Field

from .base import StrictModel


class ReportContract(StrictModel):
    company: str
    period: dict[str, str]
    language: str
    report_type: str
    required_layers: list[str]
    required_outputs: list[str]
    reasoning_chain: list[str]
    quality_rules: list[str]


class ReportSection(StrictModel):
    section_id: str
    title: str
    content_markdown: str
    evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
