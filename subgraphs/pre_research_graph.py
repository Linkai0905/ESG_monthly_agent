from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from esg_monthly_agent.nodes.pre_research import (
    build_evidence_needs,
    build_evidence_plan,
    build_materiality_topics,
    build_source_registry,
    define_report_contract,
    discover_company_boundary,
    generate_search_tasks,
    map_customer_segments,
)
from esg_monthly_agent.state import ESGReportState


def build_pre_research_graph():
    builder = StateGraph(ESGReportState)
    builder.add_node("define_report_contract", define_report_contract)
    builder.add_node("discover_company_boundary", discover_company_boundary)
    builder.add_node("map_customer_segments", map_customer_segments)
    builder.add_node("build_materiality_topics", build_materiality_topics)
    builder.add_node("build_evidence_needs", build_evidence_needs)
    builder.add_node("build_source_registry", build_source_registry)
    builder.add_node("build_evidence_plan", build_evidence_plan)
    builder.add_node("generate_search_tasks", generate_search_tasks)

    builder.add_edge(START, "define_report_contract")
    builder.add_edge("define_report_contract", "discover_company_boundary")
    builder.add_edge("discover_company_boundary", "map_customer_segments")
    builder.add_edge("map_customer_segments", "build_materiality_topics")
    builder.add_edge("build_materiality_topics", "build_evidence_needs")
    builder.add_edge("build_evidence_needs", "build_source_registry")
    builder.add_edge("build_source_registry", "build_evidence_plan")
    builder.add_edge("build_evidence_plan", "generate_search_tasks")
    builder.add_edge("generate_search_tasks", END)
    return builder.compile()
