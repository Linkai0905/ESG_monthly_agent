from __future__ import annotations

from typing import Any

from esg_monthly_agent.research_providers.openai_web_search_provider import _priority_for_url
from esg_monthly_agent.schemas import EvidenceItem, dump_model, stable_id
from esg_monthly_agent.schemas.deepsearch import DeepSearchResult, DeepSearchTask
from esg_monthly_agent.skills.common import company_name


def run(state: dict[str, Any]) -> dict[str, Any]:
    return {"evidence_items": dump_model(extract_evidence_from_deepsearch(state))}


def extract_evidence_from_deepsearch(state: dict[str, Any]) -> list[EvidenceItem]:
    tasks = {task["task_id"]: DeepSearchTask.model_validate(task) for task in state.get("deepsearch_tasks", [])}
    accepted_task_ids = {
        decision["task_id"]
        for decision in state.get("deepsearch_decisions", [])
        if decision.get("action") == "enough"
    }
    existing = {item.get("evidence_id") for item in state.get("evidence_items", [])}
    items: list[EvidenceItem] = []
    for raw_result in state.get("deepsearch_results", []):
        result = DeepSearchResult.model_validate(raw_result)
        if result.task_id not in accepted_task_ids:
            continue
        task = tasks.get(result.task_id)
        if not task:
            continue
        citations = {citation.citation_id: citation for citation in result.citations}
        for claim in result.claims:
            if claim.claim_type == "inference" or not claim.citation_ids:
                continue
            for citation_id in claim.citation_ids:
                citation = citations.get(citation_id)
                if not citation or not citation.url:
                    continue
                evidence_id = stable_id("ev", task.task_id, citation_id, claim.claim_id)
                if evidence_id in existing:
                    continue
                priority = citation.source_priority or _priority_for_url(citation.url)
                evidence_text = _citation_evidence_text(citation, claim.text, result.answer_summary)
                items.append(
                    EvidenceItem(
                        evidence_id=evidence_id,
                        source_url=citation.url,
                        source_note=f"deepsearch_claim:{result.task_id}:{claim.claim_id}",
                        source_title=citation.title,
                        publisher=citation.publisher or _publisher_from_url(citation.url),
                        publish_date=citation.publish_date,
                        text=evidence_text,
                        related_company=company_name(state),
                        related_issues=[task.issue_id],
                        layer=task.layer,
                        object_type=task.object_type,
                        esg_dimension="Mixed",
                        authority_score=0.95 if priority == "P0" else 0.8 if priority == "P1" else 0.55,
                        freshness_score=0.85,
                        relevance_score=claim.confidence,
                        source_priority=priority,
                        evidence_type=task.object_type,
                        quote=citation.snippet_or_quote or "",
                        missing_evidence=[] if priority in {"P0", "P1"} else ["需补充官方或更高可信来源交叉验证。"],
                    )
                )
    return items


def _publisher_from_url(url: str) -> str:
    return url.split("/")[2].replace("www.", "") if "://" in url else ""


def _citation_evidence_text(citation: Any, claim_text: str, answer_summary: str) -> str:
    return citation.snippet_or_quote or citation.title or claim_text or answer_summary
