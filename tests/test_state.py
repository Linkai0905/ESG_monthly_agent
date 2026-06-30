from __future__ import annotations

from esg_monthly_agent.state import ESGReportState


def test_state_contains_required_keys():
    annotations = ESGReportState.__annotations__
    for key in [
        "company",
        "evidence_needs",
        "search_tasks",
        "evidence_items",
        "issue_chains",
        "recommendations",
        "quality_checks",
        "needs_repair",
    ]:
        assert key in annotations
