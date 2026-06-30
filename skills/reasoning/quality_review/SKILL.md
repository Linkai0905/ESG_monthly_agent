---
name: quality-review
description: Review ESG monthly report state for evidence sufficiency, source quality, missing links, and repair needs.
---

# QualityReviewSkill

Checks whether the current evidence chain and report state meet the configured export conditions.

## When To Use

Runs after report synthesis and before export, or before a repair loop.

Fact creation and prose rewriting are outside this module.

## Inputs

- `state.report_markdown`
- `state.evidence_items`
- `state.source_records`
- `state.issue_chains`
- `state.company_exposures`
- `state.recommendations`
- `state.warnings`

## Outputs

- `quality_checks: QualityCheckResult`
- `needs_repair: bool`
- Schema: `QualityReviewOutput`
- Runner: `runner.py`

## Execution Contract

1. Checks cover source authority, evidence coverage, chain gaps, recommendation quality, and sample-source risk.
2. Failed checks set `needs_repair=True`.
3. Warnings include enough context for repair or manual review.
4. Report markdown is not modified here.

## Evidence And Failure Rules

- Weak-source and missing-evidence risks are not suppressed.
- Material conclusions without support do not pass.
- Sample, placeholder, or missing-URL evidence is treated as a quality risk.

## Acceptance Checks

- Output validates as `QualityCheckResult` and `needs_repair`.
- Failed checks include clear reasons.
- No report prose is generated or modified.
