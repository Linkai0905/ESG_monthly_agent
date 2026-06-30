from __future__ import annotations

from esg_monthly_agent.skills.reasoning.report_writer.runner import run as report_writer_run


def report_writer(state: dict) -> dict:
    return report_writer_run(state)
