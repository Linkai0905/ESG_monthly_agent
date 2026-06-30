from __future__ import annotations

from pydantic import Field

from esg_monthly_agent.schemas import CustomerSegment, StrictModel


class CustomerSegmentInput(StrictModel):
    state: dict = Field(default_factory=dict)


class CustomerSegmentOutput(StrictModel):
    customer_segments: list[CustomerSegment]
