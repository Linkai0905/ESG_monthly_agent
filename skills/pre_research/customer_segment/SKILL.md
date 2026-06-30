---
name: business-segment
description: Map company business segments to ESG touchpoints for monthly issue planning. The current compatibility state key remains customer_segments.
---

# BusinessSegmentSkill

Builds business-segment profiles for downstream materiality planning.

## When To Use

Runs after company boundary normalization and before materiality issue selection.

Recommendation writing and unrelated industry-news summarization are outside this module.

## Inputs

- `state.company_profile`
- optional `state.evidence_items`
- compatibility key: `state.customer_segments` represents business segments in the current schema.

## Outputs

- `customer_segments: list[CustomerSegment]`
- Schema: `CustomerSegmentOutput`
- Runner: `runner.py`

## Execution Contract

1. Each record is treated as a business segment profile; `CustomerSegment` is a legacy schema name.
2. ESG touchpoints focus on material topics such as safety, climate, resources, pollution, governance, supply chain, and community impact.
3. Segment names align with `CompanyProfile.business_segments` when available.
4. Segment mapping favors concise, material categories over broad generic labels.

## Evidence And Failure Rules

- Segment facts carry `evidence_ids` when evidence is available.
- Missing revenue drivers, geographies, or exposure points are recorded in `missing_evidence`.
- News snippets are not converted into segment conclusions.

## Acceptance Checks

- Output validates as `list[CustomerSegment]`.
- Each segment includes `segment_id`, `segment_name`, `description`, and `esg_touchpoints`.
- No report prose is emitted.
