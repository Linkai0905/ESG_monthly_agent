from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import synthesize_recommendations


def run(state: dict) -> dict:
    return {"recommendations": dump_model(synthesize_recommendations(state))}
