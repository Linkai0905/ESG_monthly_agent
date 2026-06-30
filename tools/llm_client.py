from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests

from esg_monthly_agent.config import (
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS,
)


class LLMConfigError(RuntimeError):
    pass


class LLMAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    provider: str = LLM_PROVIDER
    base_url: str = LLM_BASE_URL
    model: str = LLM_MODEL
    timeout_seconds: int = LLM_TIMEOUT_SECONDS
    max_tokens: int = LLM_MAX_TOKENS

    @property
    def endpoint(self) -> str:
        base = self.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"


def _api_key_from_env(provider: str | None = None) -> str | None:
    provider_name = (provider or "").lower()
    qwen_like = provider_name in {"qwen", "qwen-compatible", "qwen_compatible"}
    glm_like = provider_name in {"glm", "glm-compatible", "glm_compatible", "zhipu", "zhipu-compatible"}
    if qwen_like:
        names = (
            "QWEN_API_KEY",
            "ESG_QWEN_API_KEY",
            "ESG_LLM_API_KEY",
            "LLM_API_KEY",
            "DASHSCOPE_API_KEY",
            "OPENAI_API_KEY",
        )
    elif glm_like:
        names = (
            "GLM_API_KEY",
            "ESG_GLM_API_KEY",
            "ZHIPU_LLM_API_KEY",
            "BIGMODEL_LLM_API_KEY",
        )
    else:
        names = (
            "ESG_LLM_API_KEY",
            "LLM_API_KEY",
            "DEEPSEEK_API_KEY",
            "DASHSCOPE_API_KEY",
            "QWEN_API_KEY",
            "ESG_QWEN_API_KEY",
            "OPENAI_API_KEY",
        )
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def build_llm_config(state: dict[str, Any] | None = None) -> LLMConfig:
    state = state or {}
    settings = resolve_llm_settings(state)
    api_key = _api_key_from_env(settings["provider"])
    if not api_key:
        raise LLMConfigError(
            "缺少 LLM API Key。请设置 ESG_LLM_API_KEY；使用 DeepSeek 时也可设置 DEEPSEEK_API_KEY。"
        )
    return LLMConfig(
        api_key=api_key,
        provider=settings["provider"],
        base_url=settings["base_url"],
        model=settings["model"],
    )


def resolve_llm_settings(state: dict[str, Any] | None = None) -> dict[str, str]:
    state = state or {}
    provider = state.get("llm_provider") or LLM_PROVIDER
    return {
        "provider": provider,
        "base_url": state.get("llm_base_url") or _configured_base_url(provider),
        "model": state.get("llm_model") or _configured_model(provider),
    }


class OpenAICompatibleLLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        response = requests.post(
            self.config.endpoint,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        if response.status_code >= 400:
            raise LLMAPIError(_safe_error_message(response))

        data = response.json()
        choices = data.get("choices") or []
        message = (choices[0].get("message") if choices else {}) or {}
        return {
            "provider": self.config.provider,
            "status": "ok",
            "id": data.get("id"),
            "model": data.get("model") or self.config.model,
            "base_url": self.config.base_url,
            "content_markdown": message.get("content") or "",
            "finish_reason": choices[0].get("finish_reason") if choices else None,
            "usage": data.get("usage") or {},
        }


def build_report_review_messages(state: dict[str, Any]) -> list[dict[str, str]]:
    company = (state.get("company") or {}).get("name") or "目标公司"
    compact_context = {
        "company": company,
        "period": state.get("period") or {},
        "quality_checks": state.get("quality_checks") or {},
        "issue_chains": [
            {
                "issue_id": item.get("issue_id"),
                "issue_name": item.get("issue_name"),
                "missing_links": item.get("missing_links"),
                "confidence": item.get("confidence"),
            }
            for item in state.get("issue_chains", [])
        ],
        "recommendations": [
            {
                "issue_id": item.get("issue_id"),
                "priority": item.get("priority"),
                "recommendation": item.get("recommendation"),
                "evidence_ids": item.get("evidence_ids"),
            }
            for item in state.get("recommendations", [])
        ],
    }
    report = (state.get("report_markdown") or "")[:14000]
    return [
        {
            "role": "system",
            "content": (
                "你是严谨的 ESG 月报审阅助手。只能依据用户提供的报告正文和结构化对象审阅；"
                "不得新增事实、不得编造来源、不得把缺证据内容写成确定事实。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请审阅这份 ESG 月报，输出中文 Markdown，包含：\n"
                "1. 总体判断\n"
                "2. 证据链缺口\n"
                "3. 需要人工复核的高风险表述\n"
                "4. 可改进的报告结构\n\n"
                "结构化对象：\n"
                f"{json.dumps(compact_context, ensure_ascii=False, indent=2)}\n\n"
                "报告正文：\n"
                f"{report}"
            ),
        },
    ]


def _safe_error_message(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        data = response.text[:500]
    return f"LLM API 调用失败：HTTP {response.status_code} {data}"


def _configured_base_url(provider: str) -> str:
    if os.getenv("ESG_LLM_BASE_URL") or os.getenv("LLM_BASE_URL"):
        return LLM_BASE_URL
    if os.getenv("QWEN_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL"):
        return LLM_BASE_URL
    if provider == "qwen":
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if provider == "deepseek":
        return "https://api.deepseek.com"
    return LLM_BASE_URL


def _configured_model(provider: str) -> str:
    if os.getenv("ESG_LLM_MODEL") or os.getenv("LLM_MODEL"):
        return LLM_MODEL
    if os.getenv("QWEN_MODEL") or os.getenv("DASHSCOPE_MODEL"):
        return LLM_MODEL
    if provider == "qwen":
        return "qwen-plus"
    if provider == "deepseek":
        return "deepseek-v4-pro"
    return LLM_MODEL
