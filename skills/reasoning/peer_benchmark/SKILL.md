---
name: benchmark-company-action
description: Validate benchmark-company ESG actions and surface evidence-quality warnings for recommendations and report writing.
---

# BenchmarkCompanyActionSkill

Checks whether `peer_actions` are reliable enough to serve as comparison signals.

## When To Use

Runs after event classification and before recommendation generation or report writing.

Report-subject analysis is not replaced by benchmark-company actions.

## Inputs

- `state.peer_actions`
- `state.company_profile`
- `state.evidence_items`
- `state.source_records`

## Outputs

- `warnings: list[dict]`
- Schema: `PeerBenchmarkOutput`
- Runner: `runner.py`

## Execution Contract

1. `peer_actions` represents benchmark-company actions in the current internal schema.
2. Actions are checked for P0/P1 evidence support where available.
3. Weak, stale, or issue-disconnected evidence produces warnings.
4. Benchmark-company actions remain separate from report-subject company events.

## Evidence And Failure Rules

- A benchmark-company action does not imply the report subject has taken the same action.
- Unsupported benchmark claims are not used as recommendation evidence.
- Weak evidence is surfaced through warnings.

## Acceptance Checks

- Output validates as `warnings: list[dict]`.
- Warnings identify the action-quality issue.
- No report prose is emitted.
