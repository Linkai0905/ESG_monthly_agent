from __future__ import annotations

from esg_monthly_agent.skills.pre_research.company_boundary.runner import run as company_boundary_run
from esg_monthly_agent.skills.pre_research.customer_segment.runner import run as customer_segment_run
from esg_monthly_agent.skills.pre_research.evidence_need_builder.runner import run as evidence_need_run
from esg_monthly_agent.skills.pre_research.materiality_issue.runner import run as materiality_issue_run
from esg_monthly_agent.skills.pre_research.query_generation.runner import run as query_generation_run
from esg_monthly_agent.skills.pre_research.report_contract.runner import run as report_contract_run
from esg_monthly_agent.skills.pre_research.search_task_planner.runner import run as search_task_run
from esg_monthly_agent.skills.pre_research.source_registry.runner import run as source_registry_run


def define_report_contract(state: dict) -> dict:
    return report_contract_run(state)


def discover_company_boundary(state: dict) -> dict:
    return company_boundary_run(state)


def map_customer_segments(state: dict) -> dict:
    return customer_segment_run(state)


def build_materiality_topics(state: dict) -> dict:
    return materiality_issue_run(state)


def build_evidence_needs(state: dict) -> dict:
    return evidence_need_run(state)


def build_source_registry(state: dict) -> dict:
    return source_registry_run(state)


def build_evidence_plan(state: dict) -> dict:
    return search_task_run(state)


def generate_search_tasks(state: dict) -> dict:
    return query_generation_run(state)
