from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import review_quality


def run(state: dict) -> dict:
    checks = review_quality(state)
    return {"quality_checks": dump_model(checks), "needs_repair": not checks.passed}
