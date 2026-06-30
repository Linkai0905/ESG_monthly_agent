from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from esg_monthly_agent.nodes.deepsearch import (
    decide_research_next_step,
    extract_evidence_from_deepsearch,
    plan_deepsearch,
    reflect_deepsearch_result,
    refine_deepsearch_task,
    route_after_research_decision,
    run_hosted_deepsearch,
)
from esg_monthly_agent.state import ESGReportState


def build_deepsearch_research_graph():
    builder = StateGraph(ESGReportState)
    builder.add_node("plan_deepsearch", plan_deepsearch)
    builder.add_node("run_hosted_deepsearch", run_hosted_deepsearch)
    builder.add_node("reflect_deepsearch_result", reflect_deepsearch_result)
    builder.add_node("decide_research_next_step", decide_research_next_step)
    builder.add_node("refine_deepsearch_task", refine_deepsearch_task)
    builder.add_node("extract_evidence_from_deepsearch", extract_evidence_from_deepsearch)

    builder.add_edge(START, "plan_deepsearch")
    builder.add_edge("plan_deepsearch", "run_hosted_deepsearch")
    builder.add_edge("run_hosted_deepsearch", "reflect_deepsearch_result")
    builder.add_edge("reflect_deepsearch_result", "decide_research_next_step")
    builder.add_conditional_edges(
        "decide_research_next_step",
        route_after_research_decision,
        {"need_more": "refine_deepsearch_task", "done": "extract_evidence_from_deepsearch"},
    )
    builder.add_edge("refine_deepsearch_task", "run_hosted_deepsearch")
    builder.add_edge("extract_evidence_from_deepsearch", END)
    return builder.compile()
