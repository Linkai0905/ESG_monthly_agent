from __future__ import annotations

from esg_monthly_agent.skills.reasoning.peer_benchmark.runner import run as peer_benchmark_run


def peer_benchmark(state: dict) -> dict:
    return peer_benchmark_run(state)
