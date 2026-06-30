from __future__ import annotations

from esg_monthly_agent.skills.common import build_source_registry


def run(state: dict) -> dict:
    return {"source_registry": build_source_registry(state)}
