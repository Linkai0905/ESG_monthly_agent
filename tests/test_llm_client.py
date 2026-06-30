from __future__ import annotations

import pytest

from esg_monthly_agent.tools.llm_client import LLMConfig, LLMConfigError, build_llm_config


def test_llm_endpoint_uses_chat_completions():
    config = LLMConfig(api_key="test", base_url="https://api.deepseek.com")

    assert config.endpoint == "https://api.deepseek.com/chat/completions"


def test_llm_config_requires_api_key(monkeypatch):
    for name in (
        "ESG_LLM_API_KEY",
        "LLM_API_KEY",
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_API_KEY",
        "QWEN_API_KEY",
        "ESG_QWEN_API_KEY",
        "GLM_API_KEY",
        "ESG_GLM_API_KEY",
        "ZHIPU_LLM_API_KEY",
        "BIGMODEL_LLM_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(LLMConfigError):
        build_llm_config({})


def test_legacy_qwen_provider_gets_qwen_defaults(monkeypatch):
    monkeypatch.setenv("ESG_LLM_API_KEY", "test")
    for name in (
        "ESG_LLM_BASE_URL",
        "LLM_BASE_URL",
        "QWEN_BASE_URL",
        "DASHSCOPE_BASE_URL",
        "ESG_LLM_MODEL",
        "LLM_MODEL",
        "QWEN_MODEL",
        "DASHSCOPE_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    config = build_llm_config({"llm_provider": "qwen"})

    assert config.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config.model == "qwen-plus"


def test_glm_compatible_provider_requires_glm_specific_key(monkeypatch):
    monkeypatch.setenv("ESG_LLM_API_KEY", "generic-should-not-be-used")
    for name in ("GLM_API_KEY", "ESG_GLM_API_KEY", "ZHIPU_LLM_API_KEY", "BIGMODEL_LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(LLMConfigError):
        build_llm_config({"llm_provider": "glm-compatible"})


def test_glm_compatible_provider_uses_glm_key(monkeypatch):
    monkeypatch.setenv("ESG_LLM_API_KEY", "generic-should-not-be-used")
    monkeypatch.setenv("GLM_API_KEY", "glm-test-key")

    config = build_llm_config(
        {
            "llm_provider": "glm-compatible",
            "llm_model": "glm-5.2",
            "llm_base_url": "https://glm-compatible.example/v1",
        }
    )

    assert config.api_key == "glm-test-key"
    assert config.provider == "glm-compatible"
    assert config.model == "glm-5.2"
    assert config.endpoint == "https://glm-compatible.example/v1/chat/completions"
