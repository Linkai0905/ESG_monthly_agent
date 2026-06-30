from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import StrictModel
from .evidence import EvidenceItem


ResearchLayer = Literal["rule", "industry", "company", "peer"]
DeepSearchObjectType = Literal[
    "RuleChange",
    "IndustrySignal",
    "BestPractice",
    "CompanyEvent",
    "PeerAction",
]


class DeepSearchTask(StrictModel):
    task_id: str
    issue_id: str
    layer: ResearchLayer
    object_type: DeepSearchObjectType
    company: str
    period: dict
    research_goal: str
    initial_question: str
    required_evidence: list[str]
    source_policy: dict
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)
    provider: str | None = None
    must_search: bool = True
    max_search_calls: int = 8
    max_rounds: int = 3
    freshness_required: bool = True
    expected_output_schema: str
    missing_policy: Literal["give_up", "return_partial", "repair"] = "return_partial"


class DeepSearchClaim(StrictModel):
    claim_id: str
    text: str
    claim_type: Literal["rule", "industry", "company", "peer", "inference"]
    evidence_urls: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class DeepSearchCitation(StrictModel):
    citation_id: str
    title: str
    url: str
    publisher: str = ""
    publish_date: str | None = None
    page_age: str | None = None
    snippet_or_quote: str = ""
    source_priority: Literal["P0", "P1", "P2", "P3"] = "P2"


class DeepSearchResult(StrictModel):
    task_id: str
    issue_id: str
    provider: str
    status: Literal["completed", "partial", "failed"]
    answer_summary: str
    claims: list[DeepSearchClaim] = Field(default_factory=list)
    citations: list[DeepSearchCitation] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    tool_trace: list[dict] = Field(default_factory=list)
    source_coverage: dict = Field(default_factory=dict)
    missing_evidence: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    search_rounds_used: int | None = None
    tool_calls_used: int | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class ReflectionResult(StrictModel):
    task_id: str
    issue_id: str
    relevant: bool
    enough: bool
    source_quality_ok: bool
    freshness_ok: bool
    layer_coverage_ok: bool
    citation_quality_ok: bool
    covered_layers: list[str] = Field(default_factory=list)
    missing_layers: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    weak_sources: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    suggested_followup_question: str | None = None
    suggested_provider: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class ResearchDecision(StrictModel):
    task_id: str
    issue_id: str
    action: Literal["enough", "need_more", "replan", "switch_provider", "give_up"]
    reason: str
    next_task: DeepSearchTask | None = None
    missing_evidence: list[str] = Field(default_factory=list)
    stop_condition: str | None = None


class ContextBundle(StrictModel):
    task: DeepSearchTask
    deepsearch_results: list[DeepSearchResult] = Field(default_factory=list)
    accepted_evidence: list[EvidenceItem] = Field(default_factory=list)
    rejected_claims: list[dict] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    source_quality_summary: dict = Field(default_factory=dict)
    research_decisions: list[ResearchDecision] = Field(default_factory=list)
    allowed_answer_boundary: str
