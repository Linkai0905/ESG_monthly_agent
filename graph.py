from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from esg_monthly_agent.nodes.classify_events import classify_events
from esg_monthly_agent.nodes.company_exposure import assess_company_exposure
from esg_monthly_agent.nodes.execute_search import execute_issue_aware_search
from esg_monthly_agent.nodes.export_files import export_files
from esg_monthly_agent.nodes.extract_evidence import extract_evidence
from esg_monthly_agent.nodes.fetch_pages import fetch_pages
from esg_monthly_agent.nodes.init_context import init_context
from esg_monthly_agent.nodes.issue_chain_builder import build_issue_chains
from esg_monthly_agent.nodes.parse_documents import parse_documents
from esg_monthly_agent.nodes.peer_benchmark import peer_benchmark
from esg_monthly_agent.nodes.quality_review import quality_review, route_after_quality_review
from esg_monthly_agent.nodes.llm_review import llm_report_review
from esg_monthly_agent.nodes.recommendation import synthesize_recommendations
from esg_monthly_agent.nodes.report_writer import report_writer
from esg_monthly_agent.nodes.source_quality_filter import source_quality_filter
from esg_monthly_agent.nodes.targeted_repair import targeted_research_repair
from esg_monthly_agent.state import ESGReportState
from esg_monthly_agent.config import RESEARCH_MODE
from esg_monthly_agent.subgraphs.deepsearch_research_graph import build_deepsearch_research_graph
from esg_monthly_agent.subgraphs.pre_research_graph import build_pre_research_graph


def build_graph():
    pre_research_graph = build_pre_research_graph()
    deepsearch_research_graph = build_deepsearch_research_graph()
    builder = StateGraph(ESGReportState)
    builder.add_node("init_context", init_context)
    builder.add_node("pre_research_graph", pre_research_graph)
    builder.add_node("deepsearch_research_graph", deepsearch_research_graph)
    builder.add_node("execute_issue_aware_search", execute_issue_aware_search)
    builder.add_node("source_quality_filter", source_quality_filter)
    builder.add_node("fetch_pages", fetch_pages)
    builder.add_node("parse_documents", parse_documents)
    builder.add_node("extract_evidence", extract_evidence)
    builder.add_node("classify_events", classify_events)
    builder.add_node("build_issue_chains", build_issue_chains)
    builder.add_node("assess_company_exposure", assess_company_exposure)
    builder.add_node("peer_benchmark", peer_benchmark)
    builder.add_node("synthesize_recommendations", synthesize_recommendations)
    builder.add_node("quality_review", quality_review)
    builder.add_node("targeted_research_repair", targeted_research_repair)
    builder.add_node("report_writer", report_writer)
    builder.add_node("llm_report_review", llm_report_review)
    builder.add_node("export_files", export_files)

    builder.add_edge(START, "init_context")
    builder.add_edge("init_context", "pre_research_graph")
    builder.add_conditional_edges(
        "pre_research_graph",
        route_after_pre_research,
        {"deepsearch": "deepsearch_research_graph", "local": "execute_issue_aware_search"},
    )
    builder.add_edge("deepsearch_research_graph", "classify_events")
    builder.add_edge("execute_issue_aware_search", "source_quality_filter")
    builder.add_edge("source_quality_filter", "fetch_pages")
    builder.add_edge("fetch_pages", "parse_documents")
    builder.add_edge("parse_documents", "extract_evidence")
    builder.add_edge("extract_evidence", "classify_events")
    builder.add_edge("classify_events", "build_issue_chains")
    builder.add_edge("build_issue_chains", "assess_company_exposure")
    builder.add_edge("assess_company_exposure", "peer_benchmark")
    builder.add_edge("peer_benchmark", "synthesize_recommendations")
    builder.add_edge("synthesize_recommendations", "quality_review")
    builder.add_conditional_edges(
        "quality_review",
        route_after_quality_review,
        {"pass": "report_writer", "repair": "targeted_research_repair"},
    )
    builder.add_conditional_edges(
        "targeted_research_repair",
        route_after_pre_research,
        {"deepsearch": "deepsearch_research_graph", "local": "execute_issue_aware_search"},
    )
    builder.add_edge("report_writer", "llm_report_review")
    builder.add_edge("llm_report_review", "export_files")
    builder.add_edge("export_files", END)
    return builder.compile()


def run_graph(input_state: dict[str, Any]) -> ESGReportState:
    graph = build_graph()
    return graph.invoke(input_state)


def route_after_pre_research(state: dict[str, Any]) -> str:
    mode = state.get("research_mode") or state.get("source_mode") or RESEARCH_MODE
    if mode in {"web", "hosted_web", "deep_research", "hybrid"}:
        return "deepsearch"
    return "local"
