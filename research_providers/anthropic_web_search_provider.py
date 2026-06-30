from __future__ import annotations

import os
from typing import Any, Callable

import requests

from esg_monthly_agent.config import (
    ANTHROPIC_API_BASE_URL,
    ANTHROPIC_WEB_SEARCH_MODEL,
    ANTHROPIC_WEB_SEARCH_TOOL_TYPE,
)
from esg_monthly_agent.research_providers.base import (
    ProviderConfigurationError,
    ProviderRuntimeError,
)
from esg_monthly_agent.research_providers.openai_web_search_provider import (
    _priority_for_url,
    _publisher_from_url,
)
from esg_monthly_agent.schemas import stable_id
from esg_monthly_agent.schemas.deepsearch import (
    DeepSearchCitation,
    DeepSearchClaim,
    DeepSearchResult,
    DeepSearchTask,
)


class AnthropicWebSearchProvider:
    name = "anthropic_web_search"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        post: Callable[..., requests.Response] | None = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or ANTHROPIC_WEB_SEARCH_MODEL
        self.base_url = (base_url or ANTHROPIC_API_BASE_URL).rstrip("/")
        self.post = post or requests.post

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        if not self.api_key:
            raise ProviderConfigurationError(
                "Anthropic server-side web search requires ANTHROPIC_API_KEY. "
                "Do not use a normal chat-only provider as a realtime search substitute."
            )
        payload = {
            "model": self.model,
            "max_tokens": 1600,
            "messages": [{"role": "user", "content": _task_prompt(task)}],
            "tools": [_web_search_tool(task)],
        }
        response = self.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )
        if response.status_code >= 400:
            raise ProviderRuntimeError(f"Anthropic web search failed: HTTP {response.status_code} {response.text[:500]}")
        return _map_response(task, response.json(), self.name)


def _web_search_tool(task: DeepSearchTask) -> dict[str, Any]:
    tool: dict[str, Any] = {
        "type": ANTHROPIC_WEB_SEARCH_TOOL_TYPE,
        "name": "web_search",
        "max_uses": task.max_search_calls,
    }
    if task.allowed_domains:
        tool["allowed_domains"] = task.allowed_domains
    if task.blocked_domains:
        tool["blocked_domains"] = task.blocked_domains
    return tool


def _task_prompt(task: DeepSearchTask) -> str:
    return (
        "Use server-side web_search for audit-grade ESG research. Do not answer from memory.\n\n"
        f"Company: {task.company}\n"
        f"Period: {task.period}\n"
        f"Issue ID: {task.issue_id}\n"
        f"Layer: {task.layer}\n"
        f"Goal: {task.research_goal}\n"
        f"Initial question: {task.initial_question}\n"
        f"Required evidence: {task.required_evidence}\n"
        "Return citation-backed facts and state missing evidence clearly."
    )


def _map_response(task: DeepSearchTask, data: dict[str, Any], provider: str) -> DeepSearchResult:
    content = data.get("content") or []
    text_parts: list[str] = []
    citations: dict[str, DeepSearchCitation] = {}
    tool_trace: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    tool_calls = 0
    for block in content:
        block_type = block.get("type")
        if block_type == "server_tool_use":
            tool_calls += 1
            tool_trace.append(block)
        elif block_type == "web_search_tool_result":
            tool_trace.append(block)
            for item in block.get("content") or []:
                if isinstance(item, dict):
                    sources.append(item)
                    citation = _citation_from_source(task, item, len(citations) + 1)
                    citations[citation.citation_id] = citation
        elif block_type == "text":
            text = block.get("text") or ""
            if text:
                text_parts.append(text)
            for citation_block in block.get("citations") or []:
                citation = _citation_from_source(task, citation_block, len(citations) + 1)
                citations[citation.citation_id] = citation
    answer = "\n".join(text_parts).strip()
    citation_list = list(citations.values())
    claim = DeepSearchClaim(
        claim_id=stable_id("claim", task.task_id, answer[:80] or data.get("id")),
        text=answer[:1200] or "No supported answer returned.",
        claim_type=task.layer if citation_list else "inference",
        evidence_urls=[item.url for item in citation_list],
        citation_ids=[item.citation_id for item in citation_list],
        confidence=0.78 if citation_list else 0.2,
    )
    status = "completed" if answer and citation_list else "partial" if answer else "failed"
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
        missing_evidence=[] if citation_list else ["Hosted Claude web search returned no usable citations."],
        uncertainty=[] if citation_list else ["No citation-backed claim could be verified."],
        search_rounds_used=1,
        tool_calls_used=tool_calls,
        confidence=0.78 if citation_list else 0.1,
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
        snippet_or_quote=source.get("snippet") or source.get("cited_text") or source.get("text") or "",
        source_priority=_priority_for_url(url),
    )
