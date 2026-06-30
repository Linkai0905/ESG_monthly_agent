---
name: recommendation
description: Generate evidence-backed ESG management recommendations for the report subject from issue chains, exposure assessments, and benchmark-company actions.
---

# RecommendationSkill

Converts evidence chains and exposure assessments into structured ESG management recommendations.

## When To Use

Runs after issue-chain construction and company-exposure assessment, before report writing.

Evidence creation, event reclassification, and full report drafting are outside this module.

## Inputs

- `state.issue_chains`
- `state.company_exposures`
- `state.peer_actions`
- `state.evidence_items`
- `state.company_profile`

## Outputs

- `recommendations: list[Recommendation]`
- Schema: `RecommendationOutput`
- Runner: `runner.py`

## Execution Contract

1. Recommendations are tied to the report subject's material issues and exposure points.
2. Benchmark-company actions are references, not actions to copy directly.
3. Each recommendation states action, rationale, ESG value, responsible function, KPI, and time window.
4. Recommendation granularity fits a monthly management report and avoids strategic slogans.

## Evidence And Failure Rules

- News summaries are not recommendations.
- Factual rationale requires evidence IDs or issue-chain links.
- Insufficient evidence is recorded in structured fields rather than upgraded into certainty.

## Acceptance Checks

- Output validates as `list[Recommendation]`.
- Each recommendation links to at least one material issue or exposure.
- No full report prose is emitted.
