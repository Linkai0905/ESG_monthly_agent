---
name: source-registry
description: Define authority tiers for ESG monthly evidence sources. Provide source policy for search planning and quality review.
---

# SourceRegistrySkill

Maintains source priority levels from P0 to P3.

## When To Use

Runs after evidence needs are defined and before search execution.

URL fetching, document summarization, and conclusions are outside this module.

## Inputs

- `state.report_contract`
- `state.evidence_needs`
- `state.company_profile`

## Outputs

- `source_registry: list[dict]`
- Schema: `SourceRegistryOutput`
- Runner: `runner.py`

## Execution Contract

1. Regulators, exchanges, company filings, and formal reports receive priority.
2. Source policy varies by layer: rule, industry, company, and benchmark company.
3. Low-authority sources cannot stand alone for high-risk conclusions.
4. Registry entries remain structured enough for search planning.

## Evidence And Failure Rules

- No factual conclusion is created here.
- P2/P3 sources are leads or supporting context only.
- Missing source classes are preserved as gaps rather than silently replaced by weak sources.

## Acceptance Checks

- Output validates as `list[dict]`.
- P0/P1/P2/P3 levels are distinguishable.
- No recommendation or report prose is emitted.
