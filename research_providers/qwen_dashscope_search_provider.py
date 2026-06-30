from __future__ import annotations

import os
from typing import Any, Callable

import requests

from esg_monthly_agent.config import (
    QWEN_DASHSCOPE_API_URL,
    QWEN_DASHSCOPE_SEARCH_MODEL,
    QWEN_DASHSCOPE_SEARCH_STRATEGY,
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


class QwenDashScopeSearchProvider:
    name = "qwen_dashscope_search"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        api_url: str | None = None,
        search_strategy: str | None = None,
        post: Callable[..., requests.Response] | None = None,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_DASHSCOPE_API_KEY")
        self.model = model or QWEN_DASHSCOPE_SEARCH_MODEL
        self.api_url = api_url or QWEN_DASHSCOPE_API_URL
        self.search_strategy = search_strategy if search_strategy is not None else QWEN_DASHSCOPE_SEARCH_STRATEGY
        self.post = post or requests.post

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        if not self.api_key:
            raise ProviderConfigurationError(
                "Qwen DashScope hosted search requires DASHSCOPE_API_KEY or QWEN_DASHSCOPE_API_KEY. "
                "Do not use a normal chat-only provider as a realtime search substitute."
            )

        search_options: dict[str, Any] = {
            "enable_source": True,
            "enable_citation": True,
            "forced_search": task.must_search,
        }
        if self.search_strategy:
            search_options["search_strategy"] = self.search_strategy

        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是审计级 ESG 研究助手。必须使用联网搜索结果回答；"
                            "区分可引用事实和模型推断，缺证据时明确说明。"
                        ),
                    },
                    {"role": "user", "content": _task_prompt(task)},
                ]
            },
            "parameters": {
                "result_format": "message",
                "enable_search": True,
                "search_options": search_options,
            },
        }
        response = self.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        if response.status_code == 401:
            raise ProviderRuntimeError(
                "Qwen DashScope search failed: HTTP 401 InvalidApiKey. "
                "请确认 .env 中填写的是阿里云百炼/DashScope API Key，而不是普通聊天产品、OpenRouter、"
                "DeepSeek、QWEN_API_KEY 或其他兼容接口的 key。若 key 绑定新加坡/北京等工作空间，请同时设置 "
                "QWEN_DASHSCOPE_WORKSPACE_ID 和 QWEN_DASHSCOPE_REGION，或直接设置 QWEN_DASHSCOPE_API_URL。 "
                f"Original response: {response.text[:500]}"
            )
        if response.status_code >= 400:
            raise ProviderRuntimeError(
                f"Qwen DashScope search failed: HTTP {response.status_code} {response.text[:500]}"
            )
        return _map_response(task, response.json(), self.name)


def _task_prompt(task: DeepSearchTask) -> str:
    return (
        "请执行联网检索，不要仅凭模型记忆回答。\n"
        f"公司：{task.company}\n"
        f"期间：{task.period}\n"
        f"议题：{task.issue_id}\n"
        f"层级：{task.layer}\n"
        f"研究目标：{task.research_goal}\n"
        f"初始问题：{task.initial_question}\n"
        f"必须补齐的证据：{task.required_evidence}\n"
        f"优先来源政策：{task.source_policy}\n"
        f"允许域名：{task.allowed_domains}\n"
        f"屏蔽域名：{task.blocked_domains}\n"
        "请输出：1）可引用事实；2）每条事实对应来源；3）缺证据和不确定性。"
    )


def _map_response(task: DeepSearchTask, data: dict[str, Any], provider: str) -> DeepSearchResult:
    output = data.get("output") or {}
    answer = _answer_text(output)
    search_info = output.get("search_info") or data.get("search_info") or {}
    raw_results = (
        search_info.get("search_results")
        or search_info.get("sources")
        or output.get("search_results")
        or []
    )
    citations = [
        _citation_from_search_result(task, item, index + 1)
        for index, item in enumerate(raw_results)
        if _result_url(item)
    ]
    claim_type = task.layer if citations else "inference"
    claim = DeepSearchClaim(
        claim_id=stable_id("claim", task.task_id, answer[:80] or data.get("request_id")),
        text=answer[:1200] or "No supported answer returned.",
        claim_type=claim_type,
        evidence_urls=[item.url for item in citations],
        citation_ids=[item.citation_id for item in citations],
        confidence=0.76 if citations else 0.2,
    )
    status = "completed" if answer and citations else "partial" if answer else "failed"
    return DeepSearchResult(
        task_id=task.task_id,
        issue_id=task.issue_id,
        provider=provider,
        status=status,
        answer_summary=answer,
        claims=[claim] if answer else [],
        citations=citations,
        sources=raw_results,
        tool_trace=[
            {
                "type": "dashscope_search",
                "request_id": data.get("request_id"),
                "search_results_count": len(raw_results),
                "usage": data.get("usage") or {},
            }
        ],
        source_coverage={"citations": len(citations), "sources": len(raw_results)},
        missing_evidence=[] if citations else ["Qwen DashScope search returned no usable citations."],
        uncertainty=[] if citations else ["No citation-backed claim could be verified."],
        search_rounds_used=1,
        tool_calls_used=1,
        confidence=0.76 if citations else 0.1,
    )


def _answer_text(output: dict[str, Any]) -> str:
    if output.get("text"):
        return str(output["text"]).strip()
    choices = output.get("choices") or []
    parts = []
    for choice in choices:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.extend(item.get("text", "") for item in content if isinstance(item, dict))
    return "\n".join(part for part in parts if part).strip()


def _citation_from_search_result(
    task: DeepSearchTask, result: dict[str, Any], index: int
) -> DeepSearchCitation:
    url = _result_url(result)
    return DeepSearchCitation(
        citation_id=stable_id("cite", task.task_id, url, index),
        title=result.get("title") or result.get("name") or url,
        url=url,
        publisher=result.get("site_name") or result.get("publisher") or _publisher_from_url(url),
        publish_date=result.get("publish_date") or result.get("date"),
        page_age=result.get("page_age"),
        snippet_or_quote=result.get("snippet") or result.get("content") or result.get("summary") or "",
        source_priority=_priority_for_url(url),
    )


def _result_url(result: dict[str, Any]) -> str:
    return result.get("url") or result.get("link") or result.get("site_url") or ""
