from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import build_repair_tasks


class EvidenceRepairAgent:
    def invoke(self, state: dict) -> dict:
        repairs = build_repair_tasks(state)
        return {"repair_search_tasks": dump_model(repairs)}
