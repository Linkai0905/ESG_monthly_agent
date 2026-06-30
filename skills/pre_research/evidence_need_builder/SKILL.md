---
name: evidence-need-builder
description: Convert material ESG issues into explicit evidence needs for monthly research. Specify layer, source authority, freshness, and expected object type.
---

# EvidenceNeedBuilderSkill

Converts material topics into searchable evidence targets.

## When To Use

Runs after materiality issue selection and before source registry or search task planning.

Search execution, document parsing, and event classification are outside this module.

## Inputs

- `state.report_contract`
- `state.company_profile`
- `state.materiality_topics`
- `state.period`

## Outputs

- `evidence_needs: list[EvidenceNeed]`
- Schema: `EvidenceNeedBuilderOutput`
- Runner: `runner.py`

## Execution Contract

1. Evidence needs are tied to both issue and reporting period.
2. Needs are split across rule, industry, company, and benchmark-company layers where relevant.
3. Source authority, freshness, and expected structured object are explicit.
4. Needs should be answerable by auditable sources, not broad web exploration.

## Evidence And Failure Rules

- Evidence needs are not evidence.
- Missing evidence is not filled with invented facts.
- When reliable sources are uncertain, the need remains visible for search and quality checks.

## Acceptance Checks

- Output validates as `list[EvidenceNeed]`.
- Each need links to a materiality issue.
- Each need has a clear layer, evidence target, and source expectation.
