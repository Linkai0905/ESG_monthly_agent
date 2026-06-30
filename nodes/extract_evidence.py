from __future__ import annotations

from esg_monthly_agent.skills.research_execution.evidence_extraction.runner import run as extraction_run


def extract_evidence(state: dict) -> dict:
    return extraction_run(state)
