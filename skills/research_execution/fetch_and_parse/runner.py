from __future__ import annotations

from esg_monthly_agent.config import ALLOW_FETCH_IN_WEB_MODE
from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import parse_raw_documents


def fetch(state: dict) -> dict:
    mode = state.get("research_mode") or state.get("source_mode")
    if mode in {"web", "hosted_web", "deep_research"} and not ALLOW_FETCH_IN_WEB_MODE:
        raise RuntimeError(
            "fetch_pages is blocked in hosted web/deep research mode. "
            "Use hosted DeepSearch providers instead."
        )
    return {"raw_documents": []}


def parse(state: dict) -> dict:
    return {"parsed_documents": dump_model(parse_raw_documents(state))}


def run(state: dict) -> dict:
    return parse(state)
