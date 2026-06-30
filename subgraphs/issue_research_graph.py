from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from esg_monthly_agent.nodes.execute_search import execute_issue_aware_search
from esg_monthly_agent.nodes.extract_evidence import extract_evidence
from esg_monthly_agent.nodes.fetch_pages import fetch_pages
from esg_monthly_agent.nodes.parse_documents import parse_documents
from esg_monthly_agent.nodes.source_quality_filter import source_quality_filter
from esg_monthly_agent.state import ESGReportState


def build_issue_research_graph():
    builder = StateGraph(ESGReportState)
    builder.add_node("execute_issue_aware_search", execute_issue_aware_search)
    builder.add_node("source_quality_filter", source_quality_filter)
    builder.add_node("fetch_pages", fetch_pages)
    builder.add_node("parse_documents", parse_documents)
    builder.add_node("extract_evidence", extract_evidence)
    builder.add_edge(START, "execute_issue_aware_search")
    builder.add_edge("execute_issue_aware_search", "source_quality_filter")
    builder.add_edge("source_quality_filter", "fetch_pages")
    builder.add_edge("fetch_pages", "parse_documents")
    builder.add_edge("parse_documents", "extract_evidence")
    builder.add_edge("extract_evidence", END)
    return builder.compile()
