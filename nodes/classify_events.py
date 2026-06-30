from __future__ import annotations

from esg_monthly_agent.skills.reasoning.event_classification.runner import run as classification_run


def classify_events(state: dict) -> dict:
    return classification_run(state)
