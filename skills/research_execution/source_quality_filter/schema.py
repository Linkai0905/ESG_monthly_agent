from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import SourceRecord, StrictModel


class SourceQualityFilterInput(StrictModel):
    source_records: list[SourceRecord] = Field(default_factory=list)


class SourceQualityFilterOutput(StrictModel):
    source_records: list[SourceRecord] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)
