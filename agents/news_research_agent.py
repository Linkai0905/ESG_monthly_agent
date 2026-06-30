from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import execute_search_tasks
from esg_monthly_agent.skills.common import extract_evidence_items, parse_raw_documents


class NewsResearchAgent:
    """Dynamic retrieval agent.

    This agent reads issue-aware SearchTask objects and returns source/raw
    document records. It does not write report prose or final conclusions.
    """

    def invoke(self, state: dict) -> dict:
        result = execute_search_tasks(state)
        working_state = dict(state)
        working_state.update(result)
        parsed_documents = parse_raw_documents(working_state)
        working_state["parsed_documents"] = dump_model(parsed_documents)
        evidence_items = extract_evidence_items(working_state)
        result["parsed_documents"] = dump_model(parsed_documents)
        result["evidence_items"] = dump_model(evidence_items)

        if not result.get("raw_documents") or not result.get("evidence_items"):
            result["repair_needed"] = True
            observed_layers = {item.get("layer") for item in result.get("evidence_items", [])}
            result["missing_evidence_types"] = [
                layer for layer in ["rule", "industry", "company", "peer"] if layer not in observed_layers
            ] or ["unknown"]
        else:
            result["repair_needed"] = False
            result["missing_evidence_types"] = []
        return result
