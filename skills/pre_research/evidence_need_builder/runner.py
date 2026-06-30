from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import build_evidence_needs


def run(state: dict) -> dict:
    return {"evidence_needs": dump_model(build_evidence_needs(state))}
