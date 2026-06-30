from __future__ import annotations

from esg_monthly_agent.graph import build_graph


def test_no_fetch_in_hosted_web_mode(monkeypatch):
    def explode(_state):
        raise AssertionError("fetch_pages must not be called in hosted_web mode")

    monkeypatch.setattr("esg_monthly_agent.graph.fetch_pages", explode)
    graph = build_graph()
    output = graph.invoke(
        {
            "company": {"name": "中国神华"},
            "period": "2026-06",
            "research_mode": "hosted_web",
            "source_mode": "hosted_web",
            "default_research_provider": "qwen_dashscope_search",
            "max_research_rounds": 1,
        }
    )

    assert output["deepsearch_tasks"]
    assert output["deepsearch_results"]
    assert output["deepsearch_decisions"]
    assert not output["raw_documents"]
