from __future__ import annotations

from esg_monthly_agent.skills.common import classify_events


def run(state: dict) -> dict:
    return classify_events(state)
