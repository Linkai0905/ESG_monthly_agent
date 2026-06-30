---
name: company-exposure
description: Assess how classified ESG events and issue chains affect the report subject's material ESG issues.
---

# CompanyExposureSkill

Assesses ESG exposure for the report subject.

## When To Use

Runs after event classification or issue-chain construction and before recommendation generation.

New evidence creation and report writing are outside this module.

## Inputs

- `state.company_profile`
- `state.materiality_topics`
- `state.rule_changes`
- `state.industry_events`
- `state.company_events`
- `state.peer_actions`
- `state.evidence_items`

## Outputs

- `company_exposures: list[CompanyExposure]`
- Schema: `CompanyExposureOutput`
- Runner: `runner.py`

## Execution Contract

1. Exposure is assessed at material-issue level.
2. Direct company impact is distinguished from general industry context.
3. Exposure rationale links back to rule, industry, company, or benchmark-company events.
4. Evidence gaps produce conservative exposure levels.

## Evidence And Failure Rules

- Exposure rationale requires evidence IDs or event IDs.
- Weak or unrelated news does not become company exposure.
- Unreliable exposure judgments carry missing-evidence notes.

## Acceptance Checks

- Output validates as `list[CompanyExposure]`.
- Each exposure links to a materiality issue.
- No recommendation or report prose is emitted.
