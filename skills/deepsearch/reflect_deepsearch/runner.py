from __future__ import annotations

from typing import Any

from esg_monthly_agent.schemas.deepsearch import DeepSearchResult, DeepSearchTask, ReflectionResult

OFFICIAL_CONFIRMATION_PROVIDER = "tavily_official_search"


def run(task: dict[str, Any], result: dict[str, Any]) -> ReflectionResult:
    return reflect_deepsearch_result(
        DeepSearchTask.model_validate(task),
        DeepSearchResult.model_validate(result),
    )


def reflect_deepsearch_result(task: DeepSearchTask, result: DeepSearchResult) -> ReflectionResult:
    citation_count = len(result.citations)
    p0_or_p1 = [item for item in result.citations if item.source_priority in {"P0", "P1"}]
    unsupported_claims = [
        claim.claim_id for claim in result.claims if not claim.citation_ids or claim.claim_type == "inference"
    ]
    source_quality_ok = bool(p0_or_p1)
    citation_quality_ok = citation_count > 0 and len(unsupported_claims) < len(result.claims or [])
    freshness_ok = _freshness_ok(task, result)
    relevant = result.status in {"completed", "partial"} and bool(result.answer_summary)
    layer_coverage_ok = any(claim.claim_type == task.layer for claim in result.claims)
    enough = all([relevant, source_quality_ok, freshness_ok, layer_coverage_ok, citation_quality_ok])
    missing = list(result.missing_evidence)
    if not source_quality_ok:
        missing.append("缺少官方或高可信来源。")
    if not citation_quality_ok:
        missing.append("缺少可引用 citation。")
    if not freshness_ok:
        missing.append("未证明覆盖目标月份或最新时间窗口。")
    if not layer_coverage_ok:
        missing.append(f"未覆盖目标层级：{task.layer}。")
    return ReflectionResult(
        task_id=task.task_id,
        issue_id=task.issue_id,
        relevant=relevant,
        enough=enough,
        source_quality_ok=source_quality_ok,
        freshness_ok=freshness_ok,
        layer_coverage_ok=layer_coverage_ok,
        citation_quality_ok=citation_quality_ok,
        covered_layers=[task.layer] if layer_coverage_ok else [],
        missing_layers=[] if layer_coverage_ok else [task.layer],
        missing_evidence=sorted(set(missing)),
        weak_sources=[item.url for item in result.citations if item.source_priority in {"P2", "P3"}],
        unsupported_claims=unsupported_claims,
        suggested_followup_question=_followup_question(task, source_quality_ok, freshness_ok, citation_quality_ok),
        suggested_provider=_suggested_provider(task, result, source_quality_ok),
        confidence=min(result.confidence, 0.9 if enough else 0.45),
    )


def _freshness_ok(task: DeepSearchTask, result: DeepSearchResult) -> bool:
    if not task.freshness_required:
        return True
    label = str(task.period.get("label") or "")
    if not label:
        return True
    if label in result.answer_summary:
        return True
    return any((item.publish_date or "").startswith(label) for item in result.citations)


def _followup_question(
    task: DeepSearchTask,
    source_quality_ok: bool,
    freshness_ok: bool,
    citation_quality_ok: bool,
) -> str | None:
    if source_quality_ok and freshness_ok and citation_quality_ok:
        return None
    focus = []
    if not source_quality_ok:
        focus.append("官方/交易所/公司官网来源")
    if not freshness_ok:
        focus.append(f"{task.period.get('label', '')}时间窗口")
    if not citation_quality_ok:
        focus.append("可引用URL和原文片段")
    return f"请重新检索{task.company} {task.issue_id}，重点补齐{'、'.join(focus)}。"


def _suggested_provider(
    task: DeepSearchTask,
    result: DeepSearchResult,
    source_quality_ok: bool,
) -> str | None:
    if source_quality_ok:
        return None
    if result.provider == OFFICIAL_CONFIRMATION_PROVIDER:
        return None
    if not task.allowed_domains:
        return None
    return OFFICIAL_CONFIRMATION_PROVIDER
