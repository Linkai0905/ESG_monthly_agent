from esg_monthly_agent.nodes.deepsearch import _expand_tasks_for_available_providers
from esg_monthly_agent.schemas.deepsearch import DeepSearchTask


def _task() -> DeepSearchTask:
    return DeepSearchTask(
        task_id="deep_task",
        issue_id="mine_safety",
        layer="company",
        object_type="CompanyEvent",
        company="中国神华",
        period={"label": "2026-06"},
        research_goal="研究公司公告",
        initial_question="检索公司公告",
        required_evidence=["公司公告"],
        source_policy={},
        allowed_domains=["shenhuachina.com", "sse.com.cn"],
        expected_output_schema="CompanyEvent",
    )


def test_expand_tasks_uses_only_configured_hosted_providers(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-test")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_DASHSCOPE_API_KEY", raising=False)

    tasks = _expand_tasks_for_available_providers(
        [_task()],
        {
            "default_research_provider": "zhipu_web_search",
            "enabled_research_providers": [
                "openai_web_search",
                "anthropic_web_search",
                "qwen_dashscope_search",
                "zhipu_web_search",
                "tavily_official_search",
            ],
        },
    )

    assert [task.provider for task in tasks] == ["zhipu_web_search", "tavily_official_search"]
    assert [task.task_id for task in tasks] == [
        "deep_task__zhipu_web_search",
        "deep_task__tavily_official_search",
    ]
