from __future__ import annotations

from typing import Any

from esg_monthly_agent.schemas.deepsearch import (
    DeepSearchResult,
    DeepSearchTask,
    ReflectionResult,
    ResearchDecision,
)
from esg_monthly_agent.skills.deepsearch.plan_deepsearch.runner import refine_deepsearch_task


def run(
    task: dict[str, Any],
    result: dict[str, Any],
    reflection: dict[str, Any],
    current_round: int,
    max_rounds: int,
) -> ResearchDecision:
    return decide_research_next_step(
        DeepSearchTask.model_validate(task),
        DeepSearchResult.model_validate(result),
        ReflectionResult.model_validate(reflection),
        current_round,
        max_rounds,
    )


def decide_research_next_step(
    task: DeepSearchTask,
    result: DeepSearchResult,
    reflection: ReflectionResult,
    current_round: int,
    max_rounds: int,
) -> ResearchDecision:
    if reflection.enough:
        return ResearchDecision(
            task_id=task.task_id,
            issue_id=task.issue_id,
            action="enough",
            reason="Hosted result passed relevance, source quality, freshness, layer coverage, and citation checks.",
            stop_condition="evidence_ready",
        )
    if current_round >= max_rounds:
        return ResearchDecision(
            task_id=task.task_id,
            issue_id=task.issue_id,
            action="give_up",
            reason="Max research rounds reached before evidence quality was sufficient.",
            missing_evidence=reflection.missing_evidence or result.missing_evidence,
            stop_condition="max_rounds",
        )
    suggested_provider = reflection.suggested_provider
    if suggested_provider and suggested_provider != result.provider:
        next_task = refine_deepsearch_task(
            task.model_dump(mode="json"),
            reflection.suggested_followup_question,
            current_round,
            provider=suggested_provider,
        )
        return ResearchDecision(
            task_id=task.task_id,
            issue_id=task.issue_id,
            action="switch_provider",
            reason=f"Switch to {suggested_provider} for official-domain confirmation.",
            next_task=next_task,
            missing_evidence=reflection.missing_evidence,
        )

    next_task = refine_deepsearch_task(task.model_dump(mode="json"), reflection.suggested_followup_question, current_round)
    if not reflection.source_quality_ok:
        action = "need_more"
        reason = "Need another hosted search round focused on official or higher-trust sources."
    else:
        action = "need_more"
        reason = "Need another hosted search round to fix freshness, coverage, or citations."
    return ResearchDecision(
        task_id=task.task_id,
        issue_id=task.issue_id,
        action=action,
        reason=reason,
        next_task=next_task,
        missing_evidence=reflection.missing_evidence,
    )
