from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import map_customer_segments


def run(state: dict) -> dict:
    return {"customer_segments": dump_model(map_customer_segments(state))}
