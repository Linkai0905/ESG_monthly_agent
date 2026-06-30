---
name: report-contract
description: Define the monthly ESG report contract before research planning. Use at the start of the workflow to lock the report subject, period, required sections, evidence policy, and output boundary.
---

# ReportContractSkill

Defines the delivery boundary for an evidence-backed ESG monthly report.

## When To Use

Runs before company boundary, materiality, search planning, and report writing.

The module defines scope only; evidence collection, event classification, recommendations, and final prose belong to downstream skills.

## Inputs

- `state.company`
- `state.period`
- `state.language`
- `state.report_type`

## Outputs

- `report_contract: ReportContract`
- Schema: `ReportContractOutput`
- Runner: `runner.py`

## Execution Contract

1. The report subject and period are preserved from initialized state.
2. Required sections cover ESG policy/rating/standard updates, industry news and documented practice cases, company ESG impact and recommendations, and benchmark-company actions.
3. The final report is evidence-led; this contract is not a factual source.
4. Missing or ambiguous scope is kept visible for quality review.

## Evidence And Failure Rules

- No factual ESG conclusion is created here.
- Existing `evidence_ids` may be preserved, but new evidence links are not invented.
- Missing required inputs still produce a schema-valid contract so later checks can surface the gap.

## Acceptance Checks

- Output validates as `ReportContract`.
- Report-facing wording names the configured report subject and does not expose compatibility-key wording.
- No report prose is emitted.
