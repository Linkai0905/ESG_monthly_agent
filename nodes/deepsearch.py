from __future__ import annotations

import asyncio
import os
from typing import Any

from esg_monthly_agent.config import (
    DEFAULT_RESEARCH_PROVIDER,
    ENABLED_RESEARCH_PROVIDERS,
    MAX_RESEARCH_ROUNDS,
)
from esg_monthly_agent.research_providers import (
    ProviderConfigurationError,
    ProviderRuntimeError,
    get_research_provider,
)
from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.schemas.deepsearch import (
    ContextBundle,
    DeepSearchResult,
    DeepSearchTask,
    ReflectionResult,
)
from esg_monthly_agent.skills.deepsearch.decide_research_next_step.runner import (
    decide_research_next_step as decide_one,
)
from esg_monthly_agent.skills.deepsearch.plan_deepsearch.runner import plan_deepsearch_tasks
from esg_monthly_agent.skills.deepsearch.reflect_deepsearch.runner import (
    reflect_deepsearch_result as reflect_one,
)
from esg_monthly_agent.skills.research_execution.evidence_from_deepsearch.runner import (
    extract_evidence_from_deepsearch as extract_evidence,
)


def plan_deepsearch(state: dict[str, Any]) -> dict[str, Any]:
    tasks = plan_deepsearch_tasks(state)
    if state.get("call_all_available_providers"):
        tasks = _expand_tasks_for_available_providers(tasks, state)
    return {
        "deepsearch_tasks": dump_model(tasks),
        "active_deepsearch_tasks": dump_model(tasks),
        "deepsearch_loop_round": 1,
    }


def run_hosted_deepsearch(state: dict[str, Any]) -> dict[str, Any]:
    tasks = [DeepSearchTask.model_validate(task) for task in state.get("active_deepsearch_tasks", [])]
    if not tasks:
        return {}
    default_provider_name = state.get("default_research_provider") or DEFAULT_RESEARCH_PROVIDER
    enabled_providers = state.get("enabled_research_providers") or ENABLED_RESEARCH_PROVIDERS
    concurrency = max(1, int(os.getenv("ESG_DEEPSEARCH_CONCURRENCY", "6")))

    async def _run_all() -> list[DeepSearchResult]:
        semaphore = asyncio.Semaphore(concurrency)

        async def _run_one(task: DeepSearchTask) -> DeepSearchResult:
            provider_name = task.provider or default_provider_name
            if provider_name not in enabled_providers:
                return _failed_result(task, provider_name, f"Provider {provider_name} is not enabled.")
            async with semaphore:
                try:
                    return await asyncio.to_thread(_run_provider_research, provider_name, task)
                except (ProviderConfigurationError, ProviderRuntimeError) as exc:
                    return _failed_result(task, provider_name, str(exc))
                except Exception as exc:  # Keep one provider/network failure from aborting the whole run.
                    return _failed_result(task, provider_name, f"{type(exc).__name__}: {exc}")

        return list(await asyncio.gather(*[_run_one(task) for task in tasks]))

    return {"deepsearch_results": dump_model(asyncio.run(_run_all()))}


def _run_provider_research(provider_name: str, task: DeepSearchTask) -> DeepSearchResult:
    provider = get_research_provider(provider_name)
    return asyncio.run(provider.research(task))


def _expand_tasks_for_available_providers(
    tasks: list[DeepSearchTask],
    state: dict[str, Any],
) -> list[DeepSearchTask]:
    providers = _available_hosted_providers(
        state.get("enabled_research_providers") or ENABLED_RESEARCH_PROVIDERS,
        state.get("default_research_provider") or DEFAULT_RESEARCH_PROVIDER,
    )
    if len(providers) <= 1:
        return tasks
    expanded: list[DeepSearchTask] = []
    for task in tasks:
        for provider in providers:
            expanded.append(
                task.model_copy(
                    update={
                        "task_id": f"{task.task_id}__{provider}",
                        "provider": provider,
                    }
                )
            )
    return expanded


def _available_hosted_providers(enabled_providers: list[str], default_provider: str) -> list[str]:
    hosted = [
        "openai_web_search",
        "openai_deep_research",
        "anthropic_web_search",
        "qwen_dashscope_search",
        "zhipu_web_search",
        "tavily_official_search",
    ]
    candidates = [provider for provider in hosted if provider in enabled_providers and _provider_configured(provider)]
    if default_provider in enabled_providers and _provider_configured(default_provider):
        candidates.insert(0, default_provider)
    output: list[str] = []
    for provider in candidates:
        if provider not in output:
            output.append(provider)
    return output


def _provider_configured(provider: str) -> bool:
    if provider in {"openai_web_search", "openai_deep_research"}:
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "anthropic_web_search":
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    if provider == "qwen_dashscope_search":
        return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_DASHSCOPE_API_KEY"))
    if provider in {"zhipu_web_search", "zhipu_glm_web_search"}:
        return bool(os.getenv("ZHIPU_API_KEY") or os.getenv("BIGMODEL_API_KEY"))
    if provider == "tavily_official_search":
        return bool(os.getenv("TAVILY_API_KEY"))
    return False


def reflect_deepsearch_result(state: dict[str, Any]) -> dict[str, Any]:
    active_ids = {task["task_id"] for task in state.get("active_deepsearch_tasks", [])}
    reflected_ids = {item["task_id"] for item in state.get("deepsearch_reflections", [])}
    reflections: list[ReflectionResult] = []
    tasks = {task["task_id"]: DeepSearchTask.model_validate(task) for task in state.get("deepsearch_tasks", [])}
    for raw_result in state.get("deepsearch_results", []):
        if raw_result["task_id"] not in active_ids or raw_result["task_id"] in reflected_ids:
            continue
        task = tasks.get(raw_result["task_id"])
        if not task:
            continue
        reflections.append(reflect_one(task, DeepSearchResult.model_validate(raw_result)))
    return {"deepsearch_reflections": dump_model(reflections)}


def decide_research_next_step(state: dict[str, Any]) -> dict[str, Any]:
    active_ids = {task["task_id"] for task in state.get("active_deepsearch_tasks", [])}
    decided_ids = {item["task_id"] for item in state.get("deepsearch_decisions", [])}
    tasks = {task["task_id"]: DeepSearchTask.model_validate(task) for task in state.get("deepsearch_tasks", [])}
    results = {result["task_id"]: DeepSearchResult.model_validate(result) for result in state.get("deepsearch_results", [])}
    reflections = {
        reflection["task_id"]: ReflectionResult.model_validate(reflection)
        for reflection in state.get("deepsearch_reflections", [])
    }
    current_round = int(state.get("deepsearch_loop_round") or 1)
    max_rounds = int(state.get("max_research_rounds") or MAX_RESEARCH_ROUNDS)
    decisions = []
    next_tasks = []
    round_records = []
    missing = []
    for task_id in active_ids - decided_ids:
        task = tasks.get(task_id)
        result = results.get(task_id)
        reflection = reflections.get(task_id)
        if not task or not result or not reflection:
            continue
        decision = decide_one(task, result, reflection, current_round, max_rounds)
        decisions.append(decision)
        if decision.next_task and decision.action in {"need_more", "replan", "switch_provider"}:
            next_tasks.append(decision.next_task)
        if decision.action == "give_up":
            missing.append(
                {
                    "task_id": task.task_id,
                    "issue_id": task.issue_id,
                    "missing_evidence": decision.missing_evidence,
                }
            )
        round_records.append(
            {
                "task_id": task.task_id,
                "issue_id": task.issue_id,
                "provider": result.provider,
                "round_index": current_round,
                "action": decision.action,
                "why_continue_or_stop": decision.reason,
                "missing_evidence": decision.missing_evidence,
                "citations_count": len(result.citations),
                "source_quality": {
                    "ok": reflection.source_quality_ok,
                    "weak_sources": reflection.weak_sources,
                },
            }
        )
    return {
        "deepsearch_decisions": dump_model(decisions),
        "pending_deepsearch_tasks": dump_model(next_tasks),
        "deepsearch_rounds": round_records,
        "missing_evidence": missing,
    }


def refine_deepsearch_task(state: dict[str, Any]) -> dict[str, Any]:
    pending = state.get("pending_deepsearch_tasks", [])
    return {
        "active_deepsearch_tasks": pending,
        "deepsearch_tasks": pending,
        "pending_deepsearch_tasks": [],
        "deepsearch_loop_round": int(state.get("deepsearch_loop_round") or 1) + 1,
    }


def route_after_research_decision(state: dict[str, Any]) -> str:
    pending = state.get("pending_deepsearch_tasks") or []
    current_round = int(state.get("deepsearch_loop_round") or 1)
    max_rounds = int(state.get("max_research_rounds") or MAX_RESEARCH_ROUNDS)
    if pending and current_round < max_rounds:
        return "need_more"
    return "done"


def extract_evidence_from_deepsearch(state: dict[str, Any]) -> dict[str, Any]:
    evidence = extract_evidence(state)
    return {
        "evidence_items": dump_model(evidence),
        "context_bundles": dump_model(_build_context_bundles(state, evidence)),
    }


def mark_missing_evidence(state: dict[str, Any]) -> dict[str, Any]:
    return {"missing_evidence": state.get("missing_evidence", [])}


def _failed_result(task: DeepSearchTask, provider: str, message: str) -> DeepSearchResult:
    return DeepSearchResult(
        task_id=task.task_id,
        issue_id=task.issue_id,
        provider=provider,
        status="failed",
        answer_summary="",
        missing_evidence=[message],
        uncertainty=[message],
        search_rounds_used=0,
        tool_calls_used=0,
        confidence=0.0,
    )


def _build_context_bundles(state: dict[str, Any], evidence: list[Any]) -> list[ContextBundle]:
    results_by_task: dict[str, list[dict[str, Any]]] = {}
    for result in state.get("deepsearch_results", []):
        results_by_task.setdefault(result["task_id"], []).append(result)
    decisions_by_task: dict[str, list[dict[str, Any]]] = {}
    for decision in state.get("deepsearch_decisions", []):
        decisions_by_task.setdefault(decision["task_id"], []).append(decision)
    evidence_by_task: dict[str, list[Any]] = {}
    for item in evidence:
        for result in state.get("deepsearch_results", []):
            citation_urls = {citation.get("url") for citation in result.get("citations", [])}
            if item.source_url in citation_urls:
                evidence_by_task.setdefault(result["task_id"], []).append(item)
    seen_tasks: set[str] = set()
    bundles = []
    for raw_task in state.get("deepsearch_tasks", []):
        if raw_task["task_id"] in seen_tasks:
            continue
        seen_tasks.add(raw_task["task_id"])
        task = DeepSearchTask.model_validate(raw_task)
        results = [DeepSearchResult.model_validate(result) for result in results_by_task.get(task.task_id, [])]
        decisions = [item for item in decisions_by_task.get(task.task_id, [])]
        missing = []
        rejected = []
        for result in results:
            missing.extend(result.missing_evidence)
            rejected.extend(
                claim.model_dump(mode="json")
                for claim in result.claims
                if claim.claim_type == "inference" or not claim.citation_ids
            )
        bundles.append(
            ContextBundle(
                task=task,
                deepsearch_results=results,
                accepted_evidence=evidence_by_task.get(task.task_id, []),
                rejected_claims=rejected,
                missing_evidence=sorted(set(missing)),
                source_quality_summary={
                    "citations": sum(len(result.citations) for result in results),
                    "p0_p1": sum(
                        1
                        for result in results
                        for citation in result.citations
                        if citation.source_priority in {"P0", "P1"}
                    ),
                },
                research_decisions=decisions,
                allowed_answer_boundary="Only citation-backed claims may be used as factual evidence.",
            )
        )
    return bundles
