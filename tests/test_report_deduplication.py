from __future__ import annotations

from esg_monthly_agent.skills.common import classify_events, write_report


def _topic():
    return {
        "issue_id": "mine_safety",
        "issue_name": "煤矿安全生产与职业健康",
        "description": "test",
        "esg_dimensions": ["S"],
        "materiality_level": "high",
        "related_segments": ["煤炭生产"],
        "keywords": ["煤矿安全"],
    }


def _evidence(index: int, source_note: str, text: str | None = None) -> dict:
    return {
        "evidence_id": f"ev_{index}",
        "source_url": f"https://www.mem.gov.cn/doc/{index}.shtml",
        "source_local_path": "",
        "is_sample_source": False,
        "source_note": source_note,
        "source_title": f"安全生产政策 {index}",
        "publisher": "mem.gov.cn",
        "publish_date": "2026-06-10",
        "text": text or f"安全生产政策片段 {index}",
        "related_company": "中国神华",
        "related_issues": ["mine_safety"],
        "layer": "rule",
        "object_type": "RuleChange",
        "esg_dimension": "Mixed",
        "authority_score": 0.95,
        "freshness_score": 0.85,
        "relevance_score": 0.82,
        "source_priority": "P0",
        "evidence_type": "RuleChange",
        "quote": text or f"安全生产政策片段 {index}",
        "missing_evidence": [],
    }


def test_classify_events_merges_multiple_citations_from_one_deepsearch_claim():
    state = {
        "company": {"name": "中国神华"},
        "materiality_topics": [_topic()],
        "rule_changes": [],
        "industry_events": [],
        "company_events": [],
        "peer_actions": [],
        "evidence_items": [
            _evidence(1, "deepsearch_claim:task:claim_1"),
            _evidence(2, "deepsearch_claim:task:claim_1"),
            _evidence(3, "deepsearch_claim:task:claim_1"),
        ],
    }

    result = classify_events(state)

    assert len(result["rule_changes"]) == 1
    assert result["rule_changes"][0]["evidence_ids"] == ["ev_1", "ev_2", "ev_3"]


def test_report_limits_rule_events_to_three_per_issue():
    rule_changes = [
        {
            "rule_id": f"rule_{index}",
            "issue_id": "mine_safety",
            "title": "煤矿安全生产与职业健康相关规则动态",
            "rule_type": "RuleChange",
            "publisher": "mem.gov.cn",
            "publish_date": "2026-06-10",
            "summary": f"安全生产政策片段 {index}",
            "expected_impact": "需要映射到中国神华的管理要求。",
            "evidence_ids": [f"ev_{index}"],
            "source_priority": "P0",
            "missing_evidence": [],
        }
        for index in range(1, 5)
    ]
    state = {
        "company": {"name": "中国神华"},
        "period": {"start": "2026-06-01", "end": "2026-06-30"},
        "evidence_items": [_evidence(index, f"deepsearch_claim:task:claim_{index}") for index in range(1, 5)],
        "rule_changes": rule_changes,
        "industry_events": [],
        "company_events": [],
        "peer_actions": [],
        "issue_chains": [],
        "recommendations": [],
        "company_exposures": [],
        "quality_checks": {"passed": False},
    }

    report = write_report(state)["report_markdown"]
    rule_lines = [
        line
        for line in report.splitlines()
        if line.startswith("- **煤矿安全生产与职业健康相关规则动态**")
    ]

    assert len(rule_lines) == 3
