from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import extract_evidence_items


def run(state: dict) -> dict:
    return {"evidence_items": dump_model(extract_evidence_items(state))}
