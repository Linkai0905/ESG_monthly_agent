from __future__ import annotations

from pydantic import Field

from .base import Layer, SourcePriority, StrictModel


class SourceRecord(StrictModel):
    source_id: str
    task_id: str
    issue_id: str
    layer: Layer
    url: str
    local_path: str = ""
    is_sample_source: bool = False
    source_note: str = ""
    title: str
    publisher: str
    publish_date: str | None = None
    priority: SourcePriority
    source_type: str
    discovered_via: str
    authority_score: float = Field(ge=0, le=1)
    freshness_score: float = Field(default=0.7, ge=0, le=1)
    relevance_score: float = Field(default=0.7, ge=0, le=1)


class SearchTask(StrictModel):
    task_id: str
    issue_id: str
    layer: Layer
    object_type: str
    search_goal: str
    queries: list[str]
    source_priority: list[SourcePriority]
    target_sources: list[str]
    date_range: dict[str, str]
    min_results: int = 1
    min_evidence_items: int = 1
    required: bool = True
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    expected_output_schema: str
    repair_strategy: str
