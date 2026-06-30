from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import ParsedDocument, RawDocument, StrictModel


class FetchAndParseInput(StrictModel):
    raw_documents: list[RawDocument] = Field(default_factory=list)


class FetchAndParseOutput(StrictModel):
    parsed_documents: list[ParsedDocument]
