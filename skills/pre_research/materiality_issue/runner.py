from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import build_materiality_topics


def run(state: dict) -> dict:
    return {"materiality_topics": dump_model(build_materiality_topics(state))}
