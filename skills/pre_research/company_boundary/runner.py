from __future__ import annotations

from esg_monthly_agent.schemas import dump_model
from esg_monthly_agent.skills.common import discover_company_boundary


def run(state: dict) -> dict:
    profile = discover_company_boundary(state)
    return {
        "company_profile": dump_model(profile),
        "aliases": profile.aliases,
        "ticker": profile.tickers,
        "industry": profile.industry,
        "peers": profile.peers,
    }
