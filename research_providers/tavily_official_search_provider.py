from __future__ import annotations

import os
from typing import Any, Callable

import requests

from esg_monthly_agent.config import (
    TAVILY_SEARCH_API_URL,
    TAVILY_SEARCH_DEPTH,
    TAVILY_SEARCH_MAX_RESULTS,
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


class TavilyOfficialSearchProvider:
    name = "tavily_official_search"

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        search_depth: str | None = None,
        max_results: int | None = None,
        post: Callable[..., requests.Response] | None = None,
    ):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.api_url = api_url or TAVILY_SEARCH_API_URL
        self.search_depth = search_depth or TAVILY_SEARCH_DEPTH
        self.max_results = max_results or TAVILY_SEARCH_MAX_RESULTS
        self.post = post or requests.post

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        if not self.api_key:
            raise ProviderConfigurationError("Tavily official search requires TAVILY_API_KEY.")

        queries = _base_queries(task)
        domains = _ordered_domains(task)
        max_calls = max(1, task.max_search_calls)
        raw_results: list[dict[str, Any]] = []
        tool_trace: list[dict[str, Any]] = []
        for query in queries[:max_calls]:
            payload: dict[str, Any] = {
                "query": query[:400],
                "search_depth": self.search_depth,
                "max_results": min(max(1, self.max_results), 8),
                "include_answer": False,
                "include_raw_content": False,
            }
            if domains:
                payload["include_domains"] = domains
            response = self.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=90,
            )
            if response.status_code >= 400:
                raise ProviderRuntimeError(
                    f"Tavily official search failed: HTTP {response.status_code} {response.text[:500]}"
                )
            data = response.json()
            results = _raw_results(data)
            raw_results.extend(results)
            tool_trace.append(
                {
                    "type": "tavily_official_search",
                    "query": query[:400],
                    "include_domains": domains,
                    "search_results_count": len(results),
                }
            )
        return _map_results(task, _dedupe_results(raw_results), self.name, tool_trace)


def _base_queries(task: DeepSearchTask) -> list[str]:
    candidates = [item.strip() for item in task.queries if item and item.strip()]
    candidates.extend(
        [
            f"{task.company} {task.period.get('label') or ''} {task.initial_question}",
            f"{task.company} {task.issue_id} {task.layer} {task.research_goal}",
        ]
    )
    seen: set[str] = set()
    output: list[str] = []
    for item in candidates:
        cleaned = " ".join(item.split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output[:3] or [task.company]


def _ordered_domains(task: DeepSearchTask) -> list[str]:
    if not task.allowed_domains:
        return []
    preferred_by_layer = {
        "rule": ["gov.cn", "sse.com.cn", "hkexnews.hk"],
        "industry": ["gov.cn", "xinhuanet.com", "people.com.cn"],
        "company": ["shenhuachina.com", "sse.com.cn", "hkexnews.hk"],
        "peer": ["sse.com.cn", "hkexnews.hk", "cninfo.com.cn"],
    }
    preferred = preferred_by_layer.get(task.layer, [])
    domains = [domain for domain in preferred if domain in task.allowed_domains]
    domains.extend(domain for domain in task.allowed_domains if domain not in domains)
    return domains


def _raw_results(data: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = data.get("results") or data.get("search_results") or []
    return [item for item in candidates if isinstance(item, dict)]


def _map_results(
    task: DeepSearchTask,
    raw_results: list[dict[str, Any]],
    provider: str,
    tool_trace: list[dict[str, Any]],
) -> DeepSearchResult:
    official_results = [
        item
        for item in raw_results
        if _result_url(item)
        and _url_allowed(_result_url(item), task.allowed_domains)
        and _priority_for_url(_result_url(item)) in {"P0", "P1"}
        and not _is_generic_list_result(item)
    ]
    citations = [
        _citation_from_result(task, item, index + 1)
        for index, item in enumerate(official_results)
    ]
    answer = _answer_from_citations(citations) or _answer_from_results(raw_results[:1])
    claims = [_claim_from_citation(task, citation, index + 1) for index, citation in enumerate(citations)]
    if not claims and answer:
        claims = [
            DeepSearchClaim(
                claim_id=stable_id("claim", task.task_id, answer[:80] or task.initial_question),
                text=answer[:1200] or "No supported answer returned.",
                claim_type="inference",
                evidence_urls=[],
                citation_ids=[],
                confidence=0.2,
            )
        ]
    filtered_count = len([item for item in raw_results if _result_url(item)]) - len(official_results)
    missing = []
    uncertainty = []
    if not citations:
        missing.append("Tavily returned no allowed-domain P0/P1 URL citations.")
        uncertainty.append("P2 or non-allowed-domain results require official-source confirmation.")
    if filtered_count > 0:
        missing.append(f"Filtered {filtered_count} non-official or non-allowed-domain result(s) from citations.")
    return DeepSearchResult(
        task_id=task.task_id,
        issue_id=task.issue_id,
        provider=provider,
        status="completed" if citations else "partial" if raw_results else "failed",
        answer_summary=answer,
        claims=claims,
        citations=citations,
        sources=raw_results,
        tool_trace=tool_trace,
        source_coverage={
            "citations": len(citations),
            "sources": len(raw_results),
            "filtered_non_official": filtered_count,
        },
        missing_evidence=missing,
        uncertainty=uncertainty,
        search_rounds_used=len(tool_trace),
        tool_calls_used=len(tool_trace),
        confidence=0.82 if citations else 0.1,
    )


def _answer_from_results(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for index, item in enumerate(results[:5], 1):
        title = item.get("title") or "Untitled"
        publish_date = item.get("published_date") or item.get("publish_date") or item.get("date") or ""
        content = item.get("content") or item.get("snippet") or item.get("summary") or ""
        line = f"{index}. {title}"
        if publish_date:
            line += f"（{publish_date}）"
        if content:
            line += f"：{str(content).strip()[:220]}"
        parts.append(line)
    return "\n".join(parts).strip()


def _answer_from_citations(citations: list[DeepSearchCitation]) -> str:
    parts: list[str] = []
    for index, citation in enumerate(citations[:3], 1):
        text = citation.snippet_or_quote or citation.title
        parts.append(f"{index}. {citation.title}：{text[:220]}")
    return "\n".join(parts).strip()


def _claim_from_citation(task: DeepSearchTask, citation: DeepSearchCitation, index: int) -> DeepSearchClaim:
    text = citation.snippet_or_quote or citation.title
    return DeepSearchClaim(
        claim_id=stable_id("claim", task.task_id, citation.citation_id, index),
        text=text[:1200] or "No supported answer returned.",
        claim_type=task.layer,
        evidence_urls=[citation.url],
        citation_ids=[citation.citation_id],
        confidence=0.82,
    )


def _citation_from_result(task: DeepSearchTask, result: dict[str, Any], index: int) -> DeepSearchCitation:
    url = _result_url(result)
    return DeepSearchCitation(
        citation_id=stable_id("cite", task.task_id, url, index),
        title=result.get("title") or url,
        url=url,
        publisher=result.get("publisher") or _publisher_from_url(url),
        publish_date=result.get("published_date") or result.get("publish_date") or result.get("date"),
        page_age=result.get("page_age"),
        snippet_or_quote=result.get("content") or result.get("snippet") or result.get("summary") or "",
        source_priority=_priority_for_url(url),
    )


def _result_url(result: dict[str, Any]) -> str:
    return result.get("url") or result.get("link") or ""


def _url_allowed(url: str, allowed_domains: list[str]) -> bool:
    if not allowed_domains:
        return True
    return any(domain in url for domain in allowed_domains)


def _is_generic_list_result(result: dict[str, Any]) -> bool:
    url = _result_url(result).casefold()
    title = str(result.get("title") or "").strip()
    content = str(result.get("content") or result.get("snippet") or result.get("summary") or "")
    if _is_generic_title(title):
        return True
    list_url_markers = ["/index.", "/list", "list1.shtml", "/tzgg", "/xwzx", "/ywgz"]
    if any(marker in url for marker in list_url_markers) and _looks_like_navigation(content):
        return True
    return False


def _is_generic_title(title: str) -> bool:
    cleaned = " ".join(title.split()).casefold()
    generic_titles = {
        "通知公告",
        "新闻动态",
        "esg动态",
        "公告与通函",
        "信息公开",
        "首页",
    }
    if cleaned in generic_titles:
        return True
    return cleaned in {
        "通知公告 - 中华人民共和国应急管理部",
        "esg动态 - 中国神华",
    }


def _looks_like_navigation(text: str) -> bool:
    markers = ["首页", "关于我们", "新闻中心", "投资者关系", "联系我们", "网站地图", "机构设置"]
    return sum(1 for marker in markers if marker in text) >= 3


def _dedupe_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in results:
        key = _result_url(item) or f"{item.get('title', '')}|{item.get('content', '')[:80]}"
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output
