---
name: fetch-and-parse
description: Parse raw documents into structured parsed documents, and block direct fetching when hosted web/deep research mode requires provider-mediated evidence. Use after raw documents exist.
---

# FetchAndParseSkill

Parse raw documents while respecting hosted-research safety boundaries.

## When To Use

Use this skill after raw documents have been collected by search execution or local ingestion.

Do not use direct fetching in hosted web or DeepSearch mode unless configuration explicitly allows it.

## Inputs

- `state.raw_documents`
- `state.research_mode`
- `state.source_mode`
- configuration `ALLOW_FETCH_IN_WEB_MODE`

## Outputs

- `parsed_documents: list[ParsedDocument]`
- Schema: `FetchAndParseOutput` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Parse existing raw documents into normalized parsed-document records.
2. Preserve URL, title, publisher, date, text, and source metadata when available.
3. Respect the hosted web/deep research guardrail that blocks direct page fetching unless explicitly enabled.
4. Keep parsing separate from evidence judgment.

## Evidence And Failure Rules

- Parsed text is not automatically evidence.
- Do not fabricate missing document metadata.
- If fetch is blocked by mode, fail loudly with the configured runtime error rather than bypassing provider policy.

## Acceptance Checks

- Output validates as `list[ParsedDocument]`.
- Parser does not produce final report prose.
- Hosted web/deep research mode does not silently fetch pages.
