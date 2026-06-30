---
name: evidence-from-deepsearch
description: Convert accepted citation-backed DeepSearchResult claims into structured EvidenceItem records. Use after ResearchDecision.action is enough; do not extract unsupported, inference-only, or weak uncited claims as factual evidence.
---

# EvidenceFromDeepSearchSkill

Extract structured evidence from accepted hosted DeepSearch results.

## When To Use

Use this skill after the hosted research loop marks a task as `enough`.

Do not use it to convert ordinary search snippets, URL lists, model inferences, or uncited summaries into factual evidence.

## Inputs

- `state.deepsearch_tasks`
- `state.deepsearch_results`
- `state.deepsearch_decisions`
- existing `state.evidence_items`

## Outputs

- `evidence_items: list[EvidenceItem]`
- Schema export: `EvidenceItem` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Process only results whose task has an `enough` decision.
2. Extract citation-backed, non-inference claims.
3. Preserve citation URL, title, publisher, date, quote/snippet, and source priority.
4. Build evidence IDs traceable to task ID, citation ID, and claim ID.
5. Skip duplicate evidence IDs already present in state.

## Evidence And Failure Rules

- Claims without citations cannot become factual `EvidenceItem` records.
- Inference claims cannot become factual evidence.
- P2/P3 citations must carry missing-evidence notes for higher-authority verification.

## Acceptance Checks

- Output validates as `list[EvidenceItem]`.
- Every evidence item traces to a DeepSearch task and citation.
- Output contains no final report markdown.
