---
name: evidence-extraction
description: Extract structured EvidenceItem records from parsed documents and source records. Use after parsing/search execution when source text is available; do not extract unsupported claims or model-only inferences as evidence.
---

# EvidenceExtractionSkill

Extract structured evidence items from parsed research material.

## When To Use

Use this skill after raw or parsed documents are available in non-DeepSearch workflows.

Do not use it for hosted DeepSearch citation conversion; use `EvidenceFromDeepSearchSkill` for that path.

## Inputs

- `state.parsed_documents`
- `state.source_records`
- `state.search_tasks`
- `state.company_profile`
- `state.materiality_topics`

## Outputs

- `evidence_items: list[EvidenceItem]`
- Schema: `EvidenceExtractionOutput` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Extract concise, source-backed evidence tied to issue, layer, object type, and source metadata.
2. Preserve `source_url`, `source_title`, publisher, publish date, authority score, and related issues when available.
3. Keep evidence text close to the source material.
4. Assign missing-evidence notes when authority, freshness, or relevance is weak.

## Evidence And Failure Rules

- Do not convert unsupported summaries into factual evidence.
- Do not fabricate quotes, URLs, dates, or publishers.
- Avoid duplicate evidence records for the same source/task claim.

## Acceptance Checks

- Output validates as `list[EvidenceItem]`.
- Every evidence item has an evidence ID and source trace.
- Output contains no recommendations or report markdown.
