from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from esg_monthly_agent.nodes.targeted_repair import targeted_research_repair
from esg_monthly_agent.state import ESGReportState


def build_targeted_repair_graph():
    builder = StateGraph(ESGReportState)
    builder.add_node("targeted_research_repair", targeted_research_repair)
    builder.add_edge(START, "targeted_research_repair")
    builder.add_edge("targeted_research_repair", END)
    return builder.compile()
