from __future__ import annotations

from typing import Any

from esg_monthly_agent.config import MAX_RESEARCH_ROUNDS, MAX_SEARCH_CALLS_PER_TASK
from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.schemas.deepsearch import DeepSearchTask
from esg_monthly_agent.skills.common import company_name


def run(state: dict[str, Any]) -> dict[str, Any]:
    return {"deepsearch_tasks": dump_model(plan_deepsearch_tasks(state))}


def plan_deepsearch_tasks(state: dict[str, Any]) -> list[DeepSearchTask]:
    tasks = state.get("repair_search_tasks") or state.get("search_tasks") or []
    company = company_name(state)
    period = state.get("period") or {}
    output: list[DeepSearchTask] = []
    for task in tasks:
        layer = task["layer"]
        issue_id = task["issue_id"]
        source_policy = _source_policy_for_layer(layer, task)
        output.append(
            DeepSearchTask(
                task_id=f"deep_{task['task_id']}",
                issue_id=issue_id,
                layer=layer,
                object_type=_object_type(task.get("object_type") or task.get("expected_output_schema")),
                company=company,
                period=period,
                research_goal=(
                    f"围绕 issue_id={issue_id} 为{company}ESG月报收集 {layer} 层证据，"
                    "必须返回可审计引用和缺证据说明。"
                ),
                initial_question=_initial_question(task, company, period),
                required_evidence=task.get("inclusion_criteria") or [task.get("search_goal", "")],
                source_policy=source_policy,
                allowed_domains=source_policy.get("allowed_domains", []),
                blocked_domains=source_policy.get("blocked_domains", []),
                queries=task.get("queries", []),
                must_search=True,
                max_search_calls=state.get("max_search_calls_per_task") or MAX_SEARCH_CALLS_PER_TASK,
                max_rounds=state.get("max_research_rounds") or MAX_RESEARCH_ROUNDS,
                freshness_required=True,
                expected_output_schema=task.get("expected_output_schema") or task.get("object_type"),
                missing_policy="return_partial",
            )
        )
    return output


def refine_deepsearch_task(
    task: dict[str, Any],
    followup_question: str | None,
    round_index: int,
    provider: str | None = None,
) -> DeepSearchTask:
    next_task = dict(task)
    if followup_question:
        next_task["initial_question"] = followup_question
    if provider:
        next_task["provider"] = provider
    next_task["task_id"] = f"{task['task_id']}_r{round_index + 1}"
    return DeepSearchTask.model_validate(next_task)


def _initial_question(task: dict[str, Any], company: str, period: dict[str, str]) -> str:
    query_hints = "；".join(task.get("queries", [])[:3])
    return (
        f"请检索{period.get('label') or period.get('start', '')}期间与{company}相关的"
        f"{task.get('layer')}层ESG证据。研究目标：{task.get('search_goal')}。"
        f"查询提示仅作参考，不要局限于这些关键词：{query_hints}"
    )


def _source_policy_for_layer(layer: str, task: dict[str, Any]) -> dict[str, Any]:
    policy = {
        "preferred_sources": task.get("target_sources", []),
        "blocked_domains": ["zhihu.com", "baidu.com", "csdn.net", "weixin.qq.com"],
    }
    if layer == "rule":
        policy["allowed_domains"] = [
            "gov.cn",
            "sse.com.cn",
            "hkex.com.hk",
            "hkexnews.hk",
            "ifrs.org",
            "issb.org",
        ]
    elif layer == "company":
        policy["allowed_domains"] = ["shenhuachina.com", "sse.com.cn", "hkexnews.hk", "hkex.com.hk"]
    elif layer == "peer":
        policy["allowed_domains"] = ["sse.com.cn", "hkexnews.hk", "cninfo.com.cn"]
    else:
        policy["allowed_domains"] = ["gov.cn", "xinhuanet.com", "people.com.cn", "cctv.com"]
    return policy


def _object_type(value: str | None) -> str:
    if value in {"RuleChange", "IndustrySignal", "BestPractice", "CompanyEvent", "PeerAction"}:
        return value
    return "IndustrySignal"
