from __future__ import annotations

from typing import Any

from esg_monthly_agent.config import (
    DEFAULT_LANGUAGE,
    DEFAULT_REPORT_TYPE,
    DEFAULT_RESEARCH_PROVIDER,
    CALL_ALL_AVAILABLE_PROVIDERS,
    ENABLED_RESEARCH_PROVIDERS,
    MAX_RESEARCH_ROUNDS,
    MAX_SEARCH_CALLS_PER_TASK,
    RESEARCH_MODE,
    build_run_paths,
    make_run_id,
    parse_period,
)


def init_context(state: dict[str, Any]) -> dict[str, Any]:
    company_value = state.get("company") or {"name": "中国神华"}
    if isinstance(company_value, str):
        company = {"name": company_value}
    else:
        company = dict(company_value)
    company.setdefault("name", "中国神华")

    period = parse_period((state.get("period") or {}).get("label") if isinstance(state.get("period"), dict) else state.get("period"))
    if isinstance(state.get("period"), dict) and state["period"].get("start") and state["period"].get("end"):
        period = state["period"]
        period.setdefault("label", period["start"][:7])

    run_id = make_run_id(company["name"], period)
    run_paths = build_run_paths(run_id)
    return {
        "company": company,
        "period": period,
        "language": state.get("language") or DEFAULT_LANGUAGE,
        "report_type": state.get("report_type") or DEFAULT_REPORT_TYPE,
        "research_mode": state.get("research_mode") or state.get("source_mode") or RESEARCH_MODE,
        "source_mode": state.get("source_mode") or state.get("research_mode") or RESEARCH_MODE,
        "max_research_rounds": state.get("max_research_rounds") or MAX_RESEARCH_ROUNDS,
        "max_search_calls_per_task": state.get("max_search_calls_per_task") or MAX_SEARCH_CALLS_PER_TASK,
        "default_research_provider": state.get("default_research_provider") or DEFAULT_RESEARCH_PROVIDER,
        "enabled_research_providers": state.get("enabled_research_providers") or ENABLED_RESEARCH_PROVIDERS,
        "call_all_available_providers": state.get("call_all_available_providers")
        if state.get("call_all_available_providers") is not None
        else CALL_ALL_AVAILABLE_PROVIDERS,
        "ticker": state.get("ticker") or [],
        "peers": state.get("peers") or [],
        "aliases": state.get("aliases") or [],
        "industry": state.get("industry") or [],
        "run_id": run_id,
        "run_paths": {key: str(path) for key, path in run_paths.items()},
        "report_contract": {},
        "company_profile": {},
        "customer_segments": [],
        "materiality_topics": [],
        "evidence_needs": [],
        "source_registry": [],
        "search_tasks": [],
        "generated_queries": [],
        "deepsearch_tasks": [],
        "active_deepsearch_tasks": [],
        "pending_deepsearch_tasks": [],
        "deepsearch_results": [],
        "deepsearch_reflections": [],
        "deepsearch_decisions": [],
        "deepsearch_rounds": [],
        "deepsearch_loop_round": 0,
        "context_bundles": [],
        "missing_evidence": [],
        "source_records": [],
        "raw_documents": [],
        "parsed_documents": [],
        "evidence_items": [],
        "rule_changes": [],
        "industry_events": [],
        "company_events": [],
        "peer_actions": [],
        "issue_chains": [],
        "company_exposures": [],
        "recommendations": [],
        "report_sections": {},
        "report_markdown": "",
        "quality_checks": {},
        "export_paths": {},
        "errors": [],
        "warnings": [],
        "needs_repair": False,
        "repair_attempts": state.get("repair_attempts", 0),
        "repair_search_tasks": [],
    }
