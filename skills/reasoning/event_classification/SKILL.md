---
name: event-classification
description: Classify structured ESG evidence into rule changes, industry events, company events, and benchmark-company actions.
---

# EventClassificationSkill

Classifies evidence items into reasoning-ready ESG event objects.

## When To Use

Runs after evidence extraction and before issue-chain construction.

Source collection, report-section rewriting, and recommendation generation are outside this module.

## Inputs

- `state.evidence_items`
- `state.materiality_topics`
- `state.company_profile`
- `state.period`

## Outputs

- `rule_changes: list[RuleChange]`
- `industry_events: list[IndustryEvent]`
- `company_events: list[CompanyEvent]`
- `peer_actions: list[PeerAction]`, where `peer` is the internal enum for benchmark company
- Schema: `EventClassificationOutput`
- Runner: `runner.py`

## Execution Contract

1. Classification follows evidence layer and object type, not keywords alone.
2. Factual events preserve evidence IDs.
3. Benchmark-company actions stay separate from report-subject events.
4. The same evidence is duplicated only when it truly supports multiple object types.

## Evidence And Failure Rules

- Uncited inference is not classified as a factual event.
- Weak-source risks remain available for quality review.
- Ambiguous evidence is omitted or marked as a gap rather than forced into a class.

## Acceptance Checks

- All four event lists validate against schema.
- Factual events include evidence traceability.
- No report prose is emitted.
