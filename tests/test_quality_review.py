from __future__ import annotations

from esg_monthly_agent.skills.reasoning.quality_review.runner import run
from esg_monthly_agent.skills.research_execution.source_quality_filter.runner import run as source_quality_run


def test_quality_review_flags_weak_recommendation():
    state = {
        "materiality_topics": [
            {
                "issue_id": "mine_safety",
                "issue_name": "煤矿安全生产与职业健康",
                "description": "test",
                "esg_dimensions": ["S"],
                "materiality_level": "high",
                "related_segments": ["煤炭生产"],
                "keywords": ["煤矿安全"],
            }
        ],
        "issue_chains": [
            {
                "issue_id": "mine_safety",
                "issue_name": "煤矿安全生产与职业健康",
                "missing_links": [],
            }
        ],
        "company_exposures": [
            {
                "exposure_id": "exposure_1",
                "issue_id": "mine_safety",
                "affected_segments": ["煤炭生产"],
            }
        ],
        "recommendations": [
            {
                "recommendation_id": "rec_1",
                "issue_id": "mine_safety",
                "priority": "high",
                "evidence_ids": [],
                "action_owner": [],
                "suggested_kpis": [],
                "time_horizon": "",
                "related_rule_ids": [],
                "related_company_event_ids": [],
                "related_peer_action_ids": [],
            }
        ],
        "evidence_items": [],
        "repair_attempts": 0,
    }
    result = run(state)["quality_checks"]
    assert result["passed"] is False
    assert result["repairable"] is True
    assert result["weak_recommendations"]


def test_source_quality_filter_flags_low_authority_sources():
    result = source_quality_run(
        {
            "source_records": [
                {"source_id": "s1", "priority": "P3"},
                {"source_id": "s2", "priority": "P0"},
            ]
        }
    )
    assert result["warnings"]
    assert "P2/P3" in result["warnings"][0]["message"]


def test_quality_review_flags_sample_or_missing_url_sources():
    result = run(
        {
            "materiality_topics": [],
            "issue_chains": [],
            "company_exposures": [],
            "recommendations": [],
            "evidence_items": [
                {
                    "evidence_id": "ev_local",
                    "source_url": "",
                    "is_sample_source": True,
                    "publish_date": "2026-06-10",
                }
            ],
            "period": {"start": "2026-06-01", "end": "2026-06-30"},
            "repair_attempts": 0,
        }
    )["quality_checks"]
    assert result["passed"] is False
    assert result["repairable"] is False
    assert result["sample_sources"] == ["ev_local"]
