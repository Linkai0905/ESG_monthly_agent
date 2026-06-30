from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import build_repair_tasks


def targeted_research_repair(state: dict) -> dict:
    repairs = build_repair_tasks(state)
    return {
        "repair_search_tasks": dump_model(repairs),
        "search_tasks": dump_model(repairs),
        "repair_attempts": state.get("repair_attempts", 0) + 1,
        "warnings": [
            {
                "stage": "targeted_research_repair",
                "message": f"Generated {len(repairs)} repair search tasks.",
            }
        ],
    }
