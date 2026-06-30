from __future__ import annotations

from esg_monthly_agent.skills.reasoning.issue_chain_builder.runner import run


def test_issue_chain_records_missing_links():
    state = {
        "company": {"name": "中国神华"},
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
        "rule_changes": [{"rule_id": "rule_1", "issue_id": "mine_safety"}],
        "industry_events": [],
        "company_events": [],
        "peer_actions": [],
    }
    chains = run(state)["issue_chains"]
    assert chains[0]["issue_id"] == "mine_safety"
    assert "industry" in chains[0]["missing_links"]
    assert "company" in chains[0]["missing_links"]
    assert "peer" in chains[0]["missing_links"]
