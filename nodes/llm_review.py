from __future__ import annotations

from esg_monthly_agent.config import USE_LLM_REVIEW
from esg_monthly_agent.tools.llm_client import (
    LLMAPIError,
    LLMConfigError,
    OpenAICompatibleLLMClient,
    build_llm_config,
    build_report_review_messages,
    resolve_llm_settings,
)


def llm_report_review(state: dict) -> dict:
    if not (state.get("use_llm") or state.get("use_qwen") or USE_LLM_REVIEW):
        return {}

    try:
        config = build_llm_config(state)
        review = OpenAICompatibleLLMClient(config).chat(build_report_review_messages(state))
        return {"llm_review": review}
    except (LLMConfigError, LLMAPIError) as exc:
        settings = resolve_llm_settings(state)
        return {
            "llm_review": {
                "provider": settings["provider"],
                "status": "skipped",
                "error": str(exc),
                "model": settings["model"],
                "base_url": settings["base_url"],
            },
            "warnings": [{"stage": "llm_report_review", "message": str(exc)}],
        }
