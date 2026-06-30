from __future__ import annotations

from esg_monthly_agent.agents.news_research_agent import NewsResearchAgent
from esg_monthly_agent.nodes.init_context import init_context
from esg_monthly_agent.subgraphs.pre_research_graph import build_pre_research_graph


def test_news_research_agent_returns_parsed_documents_and_evidence():
    state = init_context({"company": {"name": "中国神华"}, "period": "2026-06"})
    state = build_pre_research_graph().invoke(state)
    result = NewsResearchAgent().invoke(state)
    assert result["repair_needed"] is False
    assert result["source_records"]
    assert result["raw_documents"]
    assert result["parsed_documents"]
    assert result["evidence_items"]
