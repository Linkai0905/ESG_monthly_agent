---
name: search-executor
description: Execute planned ESG SearchTask objects with configured research providers and return raw source records. Use after query generation/search planning; do not use to write conclusions or transform weak snippets into evidence.
---

# SearchExecutorSkill

Execute issue-aware search tasks and return source/raw document records.

## When To Use

Use this skill after search tasks and query hints exist.

Do not use it for final reasoning, recommendation writing, or report synthesis.

## Inputs

- `state.search_tasks`
- `state.generated_queries`
- `state.default_research_provider`
- `state.enabled_research_providers`
- `state.call_all_available_providers`
- `state.research_mode`

## Outputs

- `source_records: list[SourceRecord]`
- `raw_documents: list[RawDocument]`
- optional `warnings: list[dict]`
- Schema: `SearchExecutorOutput` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Execute only planned tasks and configured providers.
2. Preserve task IDs, issue IDs, source URLs, titles, snippets, and provider metadata.
3. When `call_all_available_providers` is true, attempt every configured available provider and surface provider failures as warnings.
4. Do not write conclusions; downstream extraction decides what becomes evidence.

## Evidence And Failure Rules

- Search results and snippets are raw material, not verified evidence.
- Do not fabricate URLs, titles, publishers, or dates.
- If a provider fails, preserve the failure context in warnings and continue where configured behavior allows.

## Acceptance Checks

- Output validates as `SearchExecutorOutput`.
- Returned records remain traceable to search tasks.
- Output contains no recommendations or report markdown.
