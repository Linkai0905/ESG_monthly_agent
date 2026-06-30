from __future__ import annotations

from esg_monthly_agent.schemas import Recommendation, SearchTask


def test_search_task_is_issue_aware():
    task = SearchTask(
        task_id="task_mine_safety_industry",
        issue_id="mine_safety",
        layer="industry",
        object_type="IndustrySignal",
        search_goal="检索煤矿安全行业信号",
        queries=["煤矿安全监管 2026 6月"],
        source_priority=["P0", "P1"],
        target_sources=["国家矿山安全监察局"],
        date_range={"start": "2026-06-01", "end": "2026-06-30"},
        expected_output_schema="IndustrySignal",
        repair_strategy="补官方来源",
    )
    assert task.issue_id == "mine_safety"
    assert "煤矿安全" in task.queries[0]


def test_recommendation_requires_operational_fields():
    rec = Recommendation(
        recommendation_id="rec_1",
        issue_id="mine_safety",
        company="中国神华",
        recommendation="建立煤矿安全生产月度 ESG 监测看板。",
        rationale="证据链显示安全生产是高重大性议题。",
        expected_esg_value="提升安全风险预警和披露可审计性。",
        action_owner=["安全生产", "ESG披露"],
        suggested_kpis=["百万工时伤害率", "隐患整改闭环率"],
        time_horizon="1-3个月",
        evidence_ids=["ev_1"],
        related_rule_ids=["rule_1"],
        related_industry_event_ids=["industry_1"],
        related_company_event_ids=["company_1"],
        related_peer_action_ids=["peer_1"],
        priority="high",
        confidence=0.8,
    )
    assert rec.evidence_ids
    assert rec.action_owner
    assert rec.suggested_kpis
