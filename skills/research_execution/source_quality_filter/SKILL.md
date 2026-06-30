---
name: source-quality-filter
description: Flag low-authority ESG source records before evidence extraction or quality review. Use after search execution to warn about P2/P3 sources and source-quality risks.
---

# SourceQualityFilterSkill

Identify weak source records and emit quality warnings.

## When To Use

Use this skill after search execution has produced `source_records`.

Do not use it to remove evidence silently or write final conclusions.

## Inputs

- `state.source_records`

## Outputs

- `warnings: list[dict]`
- Schema: `SourceQualityFilterOutput` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Identify P2/P3 records and other low-authority source risks.
2. Emit warnings that downstream reasoning and quality review can consume.
3. Preserve records for traceability; this skill currently flags rather than deletes.
4. Keep warnings concise and stage-labeled.

## Evidence And Failure Rules

- Do not allow low-authority sources alone to support high-risk ESG conclusions.
- Do not upgrade source authority without explicit metadata.
- If no source records exist, return schema-valid empty warnings.

## Acceptance Checks

- Output validates as `warnings: list[dict]`.
- Low-authority records produce a warning.
- Output contains no final report markdown.
