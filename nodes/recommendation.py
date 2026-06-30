from __future__ import annotations

from esg_monthly_agent.skills.reasoning.recommendation.runner import run as recommendation_run


def synthesize_recommendations(state: dict) -> dict:
    return recommendation_run(state)
