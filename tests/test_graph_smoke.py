from __future__ import annotations

from pathlib import Path

from esg_monthly_agent.graph import build_graph, run_graph
from esg_monthly_agent.nodes.init_context import init_context
from esg_monthly_agent.subgraphs.pre_research_graph import build_pre_research_graph


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None


def test_pre_research_graph_runs_independently():
    state = init_context({"company": {"name": "中国神华"}, "period": "2026-06"})
    output = build_pre_research_graph().invoke(state)
    issue_ids = {topic["issue_id"] for topic in output["materiality_topics"]}
    assert "climate_transition" in issue_ids
    assert "mine_safety" in issue_ids
    assert all(task["issue_id"] for task in output["search_tasks"])


def test_main_graph_smoke_generates_outputs():
    output = run_graph(
        {
            "company": {"name": "中国神华"},
            "period": "2026-06",
            "research_mode": "local_vector",
            "source_mode": "local_vector",
        }
    )
    assert output["quality_checks"]["passed"] is False
    assert output["quality_checks"]["sample_sources"]
    assert len(output["issue_chains"]) == 8
    assert output["recommendations"]
    assert output["source_records"]
    assert {record["discovered_via"] for record in output["source_records"]} == {"local_manual_sources"}
    assert not any(
        "esg-monthly-agent-seed" in item["source_url"] for item in output["evidence_items"]
    )
    assert "file://" not in output["report_markdown"]
    assert "待替换真实来源" in output["report_markdown"]
    assert "客户" not in output["report_markdown"]
    assert "目标公司" not in output["report_markdown"]
    assert "peer 对标" not in output["report_markdown"]
    assert "peer行动" not in output["report_markdown"]
    assert "### 2.4" not in output["report_markdown"]
    assert "业务板块的启示" not in output["report_markdown"]
    assert "中国神华公司动态" in output["report_markdown"]
    assert "中国神华所属行业新闻与最佳实践" in output["report_markdown"]
    assert "对标企业关键行动" in output["report_markdown"]
    report_path = Path(output["export_paths"]["report_markdown"])
    llm_review_path = Path(output["export_paths"]["llm_review"])
    sqlite_path = Path(output["export_paths"]["evidence_sqlite"])
    assert report_path.exists()
    assert llm_review_path.exists()
    assert sqlite_path.exists()
    assert "规则变化" in output["report_markdown"]
