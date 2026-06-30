from __future__ import annotations

from pydantic import Field

from .base import ESGDimension, Layer, SourcePriority, StrictModel


class EvidenceNeed(StrictModel):
    need_id: str
    issue_id: str
    layer: Layer
    object_type: str
    description: str
    required: bool = True
    preferred_sources: list[str] = Field(default_factory=list)
    min_items: int = 1
    missing_evidence: list[str] = Field(default_factory=list)


class RawDocument(StrictModel):
    document_id: str
    source_id: str
    task_id: str
    issue_id: str
    layer: Layer
    source_url: str
    source_local_path: str = ""
    is_sample_source: bool = False
    source_note: str = ""
    source_title: str
    publisher: str
    publish_date: str | None = None
    raw_text: str
    metadata: dict = Field(default_factory=dict)


class ParsedDocument(StrictModel):
    document_id: str
    source_id: str
    task_id: str
    issue_id: str
    layer: Layer
    source_url: str
    source_local_path: str = ""
    is_sample_source: bool = False
    source_note: str = ""
    source_title: str
    publisher: str
    publish_date: str | None = None
    text: str
    metadata: dict = Field(default_factory=dict)


class EvidenceItem(StrictModel):
    evidence_id: str
    source_url: str
    source_local_path: str = ""
    is_sample_source: bool = False
    source_note: str = ""
    source_title: str
    publisher: str
    publish_date: str | None = None
    text: str
    related_company: str
    related_issues: list[str]
    layer: Layer
    object_type: str
    esg_dimension: ESGDimension
    authority_score: float = Field(ge=0, le=1)
    freshness_score: float = Field(ge=0, le=1)
    relevance_score: float = Field(ge=0, le=1)
    source_priority: SourcePriority
    evidence_type: str
    quote: str = ""
    missing_evidence: list[str] = Field(default_factory=list)
