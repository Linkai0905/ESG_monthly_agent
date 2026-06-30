---
name: materiality-issue
description: Select company-specific material ESG issues for the monthly report. Use business segments and company boundary to derive focused topics for evidence planning.
---

# MaterialityIssueSkill

Selects material ESG topics for the report subject.

## When To Use

Runs after business segment mapping and before evidence need construction.

Source collection, event classification, and recommendation writing are outside this module.

## Inputs

- `state.company_profile`
- `state.customer_segments`
- `state.report_contract`
- optional `state.evidence_items`

## Outputs

- `materiality_topics: list[MaterialityTopic]`
- Schema: `MaterialityIssueOutput`
- Runner: `runner.py`

## Execution Contract

1. Topics must be specific to the report subject and its industry.
2. Policy, rating, or standard changes are included only when they affect monthly ESG interpretation.
3. Each topic should map to one or more evidence layers: rule, industry, company, or benchmark company.
4. Topic count remains small enough for traceable research and writing.

## Evidence And Failure Rules

- Materiality requires support from company profile, segment exposure, or available evidence.
- Evidence gaps are recorded instead of expanded into firm conclusions.
- No report prose is emitted.

## Acceptance Checks

- Output validates as `list[MaterialityTopic]`.
- Each topic has a stable issue identifier and ESG dimension.
- Topics fit the report-subject context.
