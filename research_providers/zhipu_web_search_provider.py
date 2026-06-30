from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

import requests

from esg_monthly_agent.config import (
    ZHIPU_WEB_SEARCH_API_URL,
    ZHIPU_WEB_SEARCH_CONTENT_SIZE,
    ZHIPU_WEB_SEARCH_COUNT,
    ZHIPU_WEB_SEARCH_ENGINE,
    ZHIPU_WEB_SEARCH_MODEL,
    ZHIPU_WEB_SEARCH_RECENCY,
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


class ZhipuWebSearchProvider:
    name = "zhipu_web_search"

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        search_engine: str | None = None,
        count: int | None = None,
        content_size: str | None = None,
        recency: str | None = None,
        post: Callable[..., requests.Response] | None = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("ZHIPU_API_KEY")
            or os.getenv("BIGMODEL_API_KEY")
            or os.getenv("GLM_API_KEY")
            or os.getenv("ESG_LLM_API_KEY")
        )
        self.api_url = api_url or ZHIPU_WEB_SEARCH_API_URL
        self.model = model or ZHIPU_WEB_SEARCH_MODEL
        self.search_engine = search_engine or ZHIPU_WEB_SEARCH_ENGINE
        self.count = count or ZHIPU_WEB_SEARCH_COUNT
        self.content_size = content_size or ZHIPU_WEB_SEARCH_CONTENT_SIZE
        self.recency = recency or ZHIPU_WEB_SEARCH_RECENCY
        self.post = post or requests.post

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        if not self.api_key:
            raise ProviderConfigurationError(
                "Zhipu web search requires ZHIPU_API_KEY or BIGMODEL_API_KEY."
            )

        if _is_openai_compatible_endpoint(self.api_url):
            return self._research_openai_compatible(task)

        payloads = _payloads_for_task(task, self.search_engine, self.count, self.recency, self.content_size)
        raw_results: list[dict[str, Any]] = []
        tool_trace: list[dict[str, Any]] = []
        for payload in payloads:
            request_payload = {key: value for key, value in payload.items() if not key.startswith("_")}
            response = self.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
                timeout=90,
            )
            if response.status_code >= 400:
                raise ProviderRuntimeError(
                    f"Zhipu web search failed: HTTP {response.status_code} {response.text[:500]}"
                )
            data = response.json()
            results = _raw_results(data)
            raw_results.extend(results)
            tool_trace.append(
                {
                    "type": "zhipu_web_search",
                    "request_id": data.get("request_id"),
                    "query": payload["search_query"],
                    "search_engine": payload.get("search_engine"),
                    "search_results_count": len(results),
                    "include_domain": payload.get("_include_domain", ""),
                }
            )
        return _map_results(task, _dedupe_results(raw_results), self.name, tool_trace)

    def _research_openai_compatible(self, task: DeepSearchTask) -> DeepSearchResult:
        payloads = _payloads_for_task(task, self.search_engine, self.count, self.recency, self.content_size)
        raw_results: list[dict[str, Any]] = []
        answers: list[str] = []
        tool_trace: list[dict[str, Any]] = []
        for payload in payloads:
            response = self.post(
                _chat_completions_url(self.api_url),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=_compatible_chat_payload(task, payload["search_query"], payload.get("_include_domain", ""), self.model),
                timeout=120,
            )
            if response.status_code >= 400:
                raise ProviderRuntimeError(
                    f"Zhipu compatible web search failed: HTTP {response.status_code} {response.text[:500]}"
                )
            data = response.json()
            content = _chat_content(data)
            parsed = _json_from_text(content)
            answer = _compatible_answer(parsed, content)
            results = _compatible_results(parsed, content)
            raw_results.extend(results)
            if answer:
                answers.append(answer)
            tool_trace.append(
                {
                    "type": "zhipu_openai_compatible_search",
                    "request_id": data.get("id") or data.get("request_id"),
                    "query": payload["search_query"],
                    "model": self.model,
                    "search_results_count": len(results),
                    "include_domain": payload.get("_include_domain", ""),
                    "usage": data.get("usage") or {},
                }
            )
        answer_summary = "\n".join(_unique_texts(answers))[:1200]
        return _map_results(
            task,
            _dedupe_results(raw_results),
            self.name,
            tool_trace,
            answer_override=answer_summary,
            no_citation_message=(
                "Zhipu OpenAI-compatible gateway returned no allowed-domain P0/P1 URL citations. "
                "The gateway may be chat-only or may not expose source URLs for web search."
            ),
        )


def _payloads_for_task(
    task: DeepSearchTask,
    search_engine: str,
    result_count: int,
    recency: str,
    content_size: str,
) -> list[dict[str, Any]]:
    queries = _base_queries(task)
    domains = _ordered_domains(task)
    max_calls = max(1, task.max_search_calls)
    search_count = min(max(1, result_count), 5)
    payloads: list[dict[str, Any]] = []
    if domains:
        for domain in domains:
            for query in queries:
                domain_query = f"{query} site:{domain}"[:180]
                payloads.append(
                    _payload(domain_query, search_engine, search_count, recency, content_size, task.task_id, domain)
                )
                if len(payloads) >= max_calls:
                    return payloads
    for query in queries:
        payloads.append(_payload(query[:180], search_engine, search_count, recency, content_size, task.task_id, ""))
        if len(payloads) >= max_calls:
            break
    return payloads


def _payload(
    query: str,
    search_engine: str,
    result_count: int,
    recency: str,
    content_size: str,
    task_id: str,
    include_domain: str,
) -> dict[str, Any]:
    return {
        "search_query": query,
        "search_engine": search_engine,
        "count": result_count,
        "search_recency_filter": recency,
        "content_size": content_size,
        "user_id": "esg-monthly-agent",
        "request_id": stable_id("zhipu_search", task_id, query),
        "_include_domain": include_domain,
    }


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


def _map_results(
    task: DeepSearchTask,
    raw_results: list[dict[str, Any]],
    provider: str,
    tool_trace: list[dict[str, Any]],
    answer_override: str | None = None,
    no_citation_message: str = "Zhipu web search returned no allowed-domain P0/P1 URL citations.",
) -> DeepSearchResult:
    official_results = [
        item
        for item in raw_results
        if _result_url(item)
        and _url_allowed(_result_url(item), task.allowed_domains)
        and _priority_for_url(_result_url(item)) in {"P0", "P1"}
    ]
    filtered_count = len([item for item in raw_results if _result_url(item)]) - len(official_results)
    citations = [
        _citation_from_result(task, item, index + 1)
        for index, item in enumerate(official_results)
    ]
    answer = (answer_override or "").strip() or _answer_from_results(official_results or raw_results)
    claim = DeepSearchClaim(
        claim_id=stable_id("claim", task.task_id, answer[:80] or task.initial_question),
        text=answer[:1200] or "No supported answer returned.",
        claim_type=task.layer if citations else "inference",
        evidence_urls=[item.url for item in citations],
        citation_ids=[item.citation_id for item in citations],
        confidence=0.8 if citations else 0.2,
    )
    status = "completed" if citations else "partial" if raw_results else "failed"
    missing = []
    uncertainty = []
    if not citations:
        missing.append(no_citation_message)
        uncertainty.append("P2 or non-allowed-domain results require a second official-source confirmation search.")
    if filtered_count > 0:
        missing.append(f"Filtered {filtered_count} non-official or non-allowed-domain result(s) from citations.")
    return DeepSearchResult(
        task_id=task.task_id,
        issue_id=task.issue_id,
        provider=provider,
        status=status,
        answer_summary=answer,
        claims=[claim] if answer else [],
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
        confidence=0.8 if citations else 0.1,
    )


def _is_openai_compatible_endpoint(api_url: str) -> bool:
    normalized = api_url.rstrip("/")
    return normalized.endswith("/v1") or normalized.endswith("/chat/completions")


def _chat_completions_url(api_url: str) -> str:
    normalized = api_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def _compatible_chat_payload(
    task: DeepSearchTask,
    query: str,
    include_domain: str,
    model: str,
) -> dict[str, Any]:
    allowed_domains = ", ".join(task.allowed_domains) or "无"
    domain_instruction = f"优先检索并引用域名 {include_domain}。" if include_domain else ""
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是审计级 ESG 研究助手。必须使用联网检索能力；不要凭模型记忆编造。"
                    "只返回 JSON，不要 Markdown。JSON 格式："
                    "{\"answer\":\"简短结论\",\"sources\":[{\"title\":\"\",\"url\":\"https://...\","
                    "\"publisher\":\"\",\"publish_date\":\"YYYY-MM-DD\",\"snippet\":\"\"}],"
                    "\"missing_evidence\":[\"...\"]}。"
                    "sources 只能包含真实可访问 URL；没有来源就返回空数组。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"检索问题：{query}\n"
                    f"公司：{task.company}\n"
                    f"期间：{task.period.get('label') or task.period}\n"
                    f"议题：{task.issue_id}\n"
                    f"层级：{task.layer}\n"
                    f"研究目标：{task.research_goal}\n"
                    f"必须证据：{task.required_evidence}\n"
                    f"允许域名：{allowed_domains}\n"
                    f"{domain_instruction}\n"
                    "请尽量使用 2026-06 或目标月份附近的官方/交易所/公司/权威来源。"
                ),
            },
        ],
        "temperature": 0.1,
        "max_tokens": 1800,
        "stream": False,
    }


def _chat_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    parts: list[str] = []
    for choice in choices:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.extend(str(item.get("text") or item.get("content") or "") for item in content if isinstance(item, dict))
    if not parts and isinstance(data.get("output_text"), str):
        parts.append(data["output_text"])
    return "\n".join(part for part in parts if part).strip()


def _json_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    for candidate in (cleaned, _json_object_slice(cleaned)):
        if not candidate:
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            return {"sources": value}
    return {}


def _json_object_slice(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def _compatible_answer(parsed: dict[str, Any], content: str) -> str:
    answer = parsed.get("answer") or parsed.get("summary") or parsed.get("text")
    if answer:
        return str(answer).strip()
    return content.strip()[:1200]


def _compatible_results(parsed: dict[str, Any], content: str) -> list[dict[str, Any]]:
    candidates = (
        parsed.get("sources")
        or parsed.get("citations")
        or parsed.get("search_results")
        or parsed.get("results")
        or []
    )
    results = [_normalize_compatible_result(item) for item in candidates if isinstance(item, dict)]
    results = [item for item in results if _result_url(item)]
    if results:
        return results
    return _results_from_urls(content)


def _normalize_compatible_result(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title") or item.get("name") or item.get("source") or item.get("url") or item.get("link"),
        "link": item.get("url") or item.get("link") or item.get("site_url"),
        "media": item.get("publisher") or item.get("site_name") or item.get("media"),
        "publish_date": item.get("publish_date") or item.get("published_date") or item.get("date"),
        "content": item.get("snippet") or item.get("quote") or item.get("content") or item.get("summary") or "",
    }


def _results_from_urls(text: str) -> list[dict[str, Any]]:
    urls = re.findall(r"https?://[^\s\]\)\}，。；；、\"'<>]+", text)
    results: list[dict[str, Any]] = []
    for url in urls:
        cleaned = url.rstrip(".,;:，。；：")
        results.append(
            {
                "title": cleaned,
                "link": cleaned,
                "media": _publisher_from_url(cleaned),
                "content": "",
            }
        )
    return results


def _unique_texts(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = " ".join(item.split())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def _raw_results(data: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = (
        data.get("search_result")
        or data.get("search_results")
        or data.get("results")
        or (data.get("data") or {}).get("search_result")
        or (data.get("data") or {}).get("results")
        or []
    )
    return [item for item in candidates if isinstance(item, dict)]


def _answer_from_results(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for index, item in enumerate(results[:5], 1):
        title = item.get("title") or "Untitled"
        publish_date = item.get("publish_date") or item.get("date") or ""
        content = item.get("content") or item.get("snippet") or item.get("summary") or ""
        line = f"{index}. {title}"
        if publish_date:
            line += f"（{publish_date}）"
        if content:
            line += f"：{str(content).strip()[:220]}"
        parts.append(line)
    return "\n".join(parts).strip()


def _citation_from_result(task: DeepSearchTask, result: dict[str, Any], index: int) -> DeepSearchCitation:
    url = _result_url(result)
    return DeepSearchCitation(
        citation_id=stable_id("cite", task.task_id, url, index),
        title=result.get("title") or url,
        url=url,
        publisher=result.get("media") or result.get("publisher") or _publisher_from_url(url),
        publish_date=result.get("publish_date") or result.get("date"),
        page_age=result.get("page_age"),
        snippet_or_quote=result.get("content") or result.get("snippet") or result.get("summary") or "",
        source_priority=_priority_for_url(url),
    )


def _result_url(result: dict[str, Any]) -> str:
    return result.get("link") or result.get("url") or result.get("site_url") or ""


def _url_allowed(url: str, allowed_domains: list[str]) -> bool:
    if not allowed_domains:
        return True
    return any(domain in url for domain in allowed_domains)


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
