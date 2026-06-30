from __future__ import annotations

from esg_monthly_agent.skills.common import benchmark_peers


def run(state: dict) -> dict:
    return benchmark_peers(state)
