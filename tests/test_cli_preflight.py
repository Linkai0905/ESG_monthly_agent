from __future__ import annotations

from datetime import date

from esg_monthly_agent.main import previous_month_label, validate_research_provider_config


def test_previous_month_label_uses_previous_complete_month():
    assert previous_month_label(date(2026, 6, 30)) == "2026-05"
    assert previous_month_label(date(2026, 1, 1)) == "2025-12"


def test_hosted_web_cli_preflight_requires_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    error = validate_research_provider_config(
        {
            "research_mode": "hosted_web",
            "default_research_provider": "openai_web_search",
        }
    )

    assert error
    assert "OPENAI_API_KEY" in error


def test_local_vector_cli_preflight_allows_no_hosted_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    error = validate_research_provider_config(
        {
            "research_mode": "local_vector",
            "default_research_provider": "local_vector",
        }
    )

    assert error is None


def test_qwen_dashscope_cli_preflight_requires_dashscope_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    error = validate_research_provider_config(
        {
            "research_mode": "hosted_web",
            "default_research_provider": "qwen_dashscope_search",
        }
    )

    assert error
    assert "DASHSCOPE_API_KEY" in error


def test_qwen_dashscope_cli_preflight_rejects_generic_qwen_chat_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("QWEN_API_KEY", "qwen-compatible-chat-key")

    error = validate_research_provider_config(
        {
            "research_mode": "hosted_web",
            "default_research_provider": "qwen_dashscope_search",
        }
    )

    assert error
    assert "QWEN_DASHSCOPE_API_KEY" in error


def test_zhipu_web_search_cli_preflight_requires_zhipu_key(monkeypatch):
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("BIGMODEL_API_KEY", raising=False)

    error = validate_research_provider_config(
        {
            "research_mode": "hosted_web",
            "default_research_provider": "zhipu_web_search",
        }
    )

    assert error
    assert "ZHIPU_API_KEY" in error


def test_tavily_official_search_cli_preflight_requires_tavily_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    error = validate_research_provider_config(
        {
            "research_mode": "hosted_web",
            "default_research_provider": "tavily_official_search",
        }
    )

    assert error
    assert "TAVILY_API_KEY" in error
