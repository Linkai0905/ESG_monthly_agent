from __future__ import annotations

from typing import Literal

from esg_monthly_agent.skills.reasoning.quality_review.runner import run as quality_review_run


def quality_review(state: dict) -> dict:
    return quality_review_run(state)


def route_after_quality_review(state: dict) -> Literal["pass", "repair"]:
    checks = state.get("quality_checks") or {}
    if checks.get("passed"):
        return "pass"
    mode = state.get("research_mode") or state.get("source_mode")
    if mode in {"web", "hosted_web", "deep_research", "hybrid"}:
        return "pass"
    if checks.get("repairable", False) and state.get("repair_attempts", 0) < 1:
        return "repair"
    return "pass"
