from __future__ import annotations

import operator
from typing import Annotated, Any
from typing_extensions import TypedDict


class ESGReportState(TypedDict, total=False):
    company: dict[str, Any]
    aliases: list[str]
    ticker: list[str]
    industry: list[str]
    peers: list[str]
    period: dict[str, str]
    language: str
    report_type: str
    research_mode: str
    source_mode: str
    max_research_rounds: int
    max_search_calls_per_task: int
    default_research_provider: str
    enabled_research_providers: list[str]
    call_all_available_providers: bool
    use_llm: bool
    llm_provider: str
    llm_model: str
    llm_base_url: str
    use_qwen: bool

    report_contract: dict[str, Any]
    company_profile: dict[str, Any]
    customer_segments: list[dict[str, Any]]
    materiality_topics: list[dict[str, Any]]
    evidence_needs: Annotated[list[dict[str, Any]], operator.add]
    source_registry: list[dict[str, Any]]
    search_tasks: Annotated[list[dict[str, Any]], operator.add]
    generated_queries: Annotated[list[dict[str, Any]], operator.add]
    deepsearch_tasks: Annotated[list[dict[str, Any]], operator.add]
    active_deepsearch_tasks: list[dict[str, Any]]
    pending_deepsearch_tasks: list[dict[str, Any]]
    deepsearch_results: Annotated[list[dict[str, Any]], operator.add]
    deepsearch_reflections: Annotated[list[dict[str, Any]], operator.add]
    deepsearch_decisions: Annotated[list[dict[str, Any]], operator.add]
    deepsearch_rounds: Annotated[list[dict[str, Any]], operator.add]
    deepsearch_loop_round: int
    context_bundles: list[dict[str, Any]]
    missing_evidence: Annotated[list[dict[str, Any]], operator.add]

    source_records: Annotated[list[dict[str, Any]], operator.add]
    raw_documents: Annotated[list[dict[str, Any]], operator.add]
    parsed_documents: Annotated[list[dict[str, Any]], operator.add]
    evidence_items: Annotated[list[dict[str, Any]], operator.add]

    rule_changes: Annotated[list[dict[str, Any]], operator.add]
    industry_events: Annotated[list[dict[str, Any]], operator.add]
    company_events: Annotated[list[dict[str, Any]], operator.add]
    peer_actions: Annotated[list[dict[str, Any]], operator.add]

    issue_chains: list[dict[str, Any]]
    company_exposures: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]

    report_sections: dict[str, Any]
    report_markdown: str
    llm_review: dict[str, Any]
    quality_checks: dict[str, Any]
    export_paths: dict[str, str]

    errors: Annotated[list[dict[str, Any]], operator.add]
    warnings: Annotated[list[dict[str, Any]], operator.add]
    needs_repair: bool
    repair_attempts: int
    repair_search_tasks: Annotated[list[dict[str, Any]], operator.add]
    run_id: str
    run_paths: dict[str, str]
