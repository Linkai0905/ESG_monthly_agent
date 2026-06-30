from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import ReportSection, StrictModel


class ReportWriterInput(StrictModel):
    state: dict = Field(default_factory=dict)


class ReportWriterOutput(StrictModel):
    report_sections: dict[str, ReportSection] = Field(default_factory=dict)
    report_markdown: str
