from __future__ import annotations

import os
from typing import Any, Callable

import requests

from esg_monthly_agent.config import (
    OPENAI_ALLOW_UNLIMITED_DEEP_RESEARCH_TOKENS,
    OPENAI_BACKGROUND_RESEARCH,
    OPENAI_RESPONSES_BASE_URL,
    OPENAI_WEB_SEARCH_MODEL,
)
from esg_monthly_agent.research_providers.base import (
    ProviderConfigurationError,
    ProviderRuntimeError,
)
from esg_monthly_agent.schemas import stable_id
from esg_monthly_agent.schemas.deepsearch import (
    DeepSearchCitation,
    DeepSearchClaim,
    DeepSearchResult,
    DeepSearchTask,
)


class OpenAIWebSearchProvider:
    name = "openai_web_search"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        post: Callable[..., requests.Response] | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or OPENAI_WEB_SEARCH_MODEL
        self.base_url = (base_url or OPENAI_RESPONSES_BASE_URL).rstrip("/")
        self.post = post or requests.post

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        if not self.api_key:
            raise ProviderConfigurationError(
                "OpenAI hosted web search requires OPENAI_API_KEY. "
                "Do not use a normal chat-only provider as a realtime search substitute."
            )

        payload = {
            "model": self.model,
            "input": _task_prompt(task),
            "tools": [_web_search_tool(task)],
            "tool_choice": "required" if task.must_search else "auto",
            "include": ["web_search_call.results"],
            "background": OPENAI_BACKGROUND_RESEARCH,
        }
        response = self.post(
            f"{self.base_url}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )
        if response.status_code >= 400:
            raise ProviderRuntimeError(f"OpenAI web search failed: HTTP {response.status_code} {response.text[:500]}")
        return _map_response(task, response.json(), self.name)


def _web_search_tool(task: DeepSearchTask) -> dict[str, Any]:
    tool: dict[str, Any] = {
        "type": "web_search",
        "search_context_size": "high" if task.layer in {"rule", "company", "peer"} else "medium",
    }
    filters = {}
    if task.allowed_domains:
        filters["allowed_domains"] = task.allowed_domains
    if task.blocked_domains:
        filters["blocked_domains"] = task.blocked_domains
    if filters:
        tool["filters"] = filters
    if OPENAI_ALLOW_UNLIMITED_DEEP_RESEARCH_TOKENS:
        tool["return_token_budget"] = "unlimited"
    return tool


def _task_prompt(task: DeepSearchTask) -> str:
    return (
        "You are performing hosted web research for an audit-grade ESG monthly report. "
        "Use the hosted web_search tool; do not rely on memory. Return concise findings with citations.\n\n"
        f"Company: {task.company}\n"
        f"Period: {task.period}\n"
        f"Issue ID: {task.issue_id}\n"
        f"Layer: {task.layer}\n"
        f"Goal: {task.research_goal}\n"
        f"Initial question: {task.initial_question}\n"
        f"Required evidence: {task.required_evidence}\n"
        f"Allowed domains: {task.allowed_domains}\n"
        f"Blocked domains: {task.blocked_domains}\n"
        "Separate directly cited facts from inference. If evidence is missing, say so."
    )


def _map_response(task: DeepSearchTask, data: dict[str, Any], provider: str) -> DeepSearchResult:
    output = data.get("output") or []
    text_parts: list[str] = []
    citations: dict[str, DeepSearchCitation] = {}
    tool_trace: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    tool_calls = 0

    for item in output:
        item_type = item.get("type")
        if item_type == "web_search_call":
            tool_calls += 1
            action = item.get("action") or {}
            tool_trace.append({"type": item_type, "status": item.get("status"), "action": action})
            for source in (item.get("results") or action.get("sources") or []):
                sources.append(source)
                citation = _citation_from_source(task, source, len(citations) + 1)
                citations[citation.citation_id] = citation
        if item_type == "message":
            for content in item.get("content") or []:
                text = content.get("text") or ""
                if text:
                    text_parts.append(text)
                for annotation in content.get("annotations") or []:
                    citation = _citation_from_annotation(task, annotation, len(citations) + 1)
                    if citation:
                        citations[citation.citation_id] = citation

    answer = "\n".join(text_parts).strip()
    citation_list = list(citations.values())
    claim_type = task.layer if citation_list else "inference"
    claim = DeepSearchClaim(
        claim_id=stable_id("claim", task.task_id, answer[:80] or data.get("id")),
        text=answer[:1200] or "No supported answer returned.",
        claim_type=claim_type,
        evidence_urls=[item.url for item in citation_list],
        citation_ids=[item.citation_id for item in citation_list],
        confidence=0.78 if citation_list else 0.2,
    )
    status = "completed" if answer and citation_list else "partial" if answer else "failed"
    missing = [] if citation_list else ["Hosted web search returned no usable citations."]
    return DeepSearchResult(
        task_id=task.task_id,
        issue_id=task.issue_id,
        provider=provider,
        status=status,
        answer_summary=answer,
        claims=[claim] if answer else [],
        citations=citation_list,
        sources=sources,
        tool_trace=tool_trace,
        source_coverage={"citations": len(citation_list), "sources": len(sources)},
        missing_evidence=missing,
        uncertainty=[] if citation_list else ["No citation-backed claim could be verified."],
        search_rounds_used=1,
        tool_calls_used=tool_calls,
        confidence=0.78 if citation_list else 0.1,
    )


def _citation_from_annotation(
    task: DeepSearchTask, annotation: dict[str, Any], index: int
) -> DeepSearchCitation | None:
    url = annotation.get("url") or annotation.get("uri")
    if not url:
        return None
    return DeepSearchCitation(
        citation_id=stable_id("cite", task.task_id, url, index),
        title=annotation.get("title") or url,
        url=url,
        publisher=_publisher_from_url(url),
        snippet_or_quote=annotation.get("text") or "",
        source_priority=_priority_for_url(url),
    )


def _citation_from_source(task: DeepSearchTask, source: dict[str, Any], index: int) -> DeepSearchCitation:
    url = source.get("url") or source.get("uri") or ""
    return DeepSearchCitation(
        citation_id=stable_id("cite", task.task_id, url or source.get("title"), index),
        title=source.get("title") or url or "Untitled source",
        url=url,
        publisher=source.get("publisher") or _publisher_from_url(url),
        publish_date=source.get("publish_date") or source.get("date"),
        page_age=source.get("page_age"),
        snippet_or_quote=source.get("snippet") or source.get("text") or "",
        source_priority=_priority_for_url(url),
    )


def _publisher_from_url(url: str) -> str:
    return url.split("/")[2].replace("www.", "") if "://" in url else ""


def _priority_for_url(url: str) -> str:
    p0_domains = ["gov.cn", "sse.com.cn", "hkexnews.hk", "shenhuachina.com", "cninfo.com.cn"]
    p1_domains = ["xinhuanet.com", "people.com.cn", "cctv.com"]
    if any(domain in url for domain in p0_domains):
        return "P0"
    if any(domain in url for domain in p1_domains):
        return "P1"
    return "P2"
