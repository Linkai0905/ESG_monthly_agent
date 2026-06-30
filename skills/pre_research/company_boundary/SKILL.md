---
name: company-boundary
description: Build the company profile boundary for ESG monthly research. Normalize name, aliases, tickers, industry, business boundary, and benchmark companies for evidence planning.
---

# CompanyBoundarySkill

Normalizes the report subject into a research-ready `CompanyProfile`.

## When To Use

Runs after `ReportContractSkill` and before business segment mapping or evidence planning.

News classification, recommendation writing, and unsupported company facts are outside this module.

## Inputs

- `state.company`
- `state.aliases`
- `state.ticker`
- `state.industry`
- `state.peers`
- optional `state.evidence_items`

## Outputs

- `company_profile: CompanyProfile`
- compatibility state keys: `aliases`, `ticker`, `industry`, `peers`
- Schema: `CompanyBoundaryOutput`
- Runner: `runner.py`

## Execution Contract

1. Names, aliases, and tickers are normalized without changing the report subject.
2. Industry and boundary notes follow disclosed business scope.
3. Supplied benchmark-company names are preserved unless state explicitly changes them.
4. Unsupported boundary facts are recorded in `missing_evidence`.

## Evidence And Failure Rules

- Boundary facts such as listing venue, industry, and business scope should carry `evidence_ids` when available.
- Subsidiaries, assets, projects, or geographies are not inferred from generic industry knowledge.
- With insufficient evidence, the profile remains conservative and the gap is explicit.

## Acceptance Checks

- Output validates as `CompanyProfile`.
- `company_profile.company` matches the report subject.
- No report prose is emitted.
