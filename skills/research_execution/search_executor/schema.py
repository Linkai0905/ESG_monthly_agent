from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import RawDocument, SourceRecord, StrictModel


class SearchExecutorInput(StrictModel):
    state: dict = Field(default_factory=dict)


class SearchExecutorOutput(StrictModel):
    source_records: list[SourceRecord]
    raw_documents: list[RawDocument]
    warnings: list[dict] = Field(default_factory=list)
