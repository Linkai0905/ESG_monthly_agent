---
name: reflect-deepsearch
description: Evaluate hosted DeepSearchResult quality for ESG evidence sufficiency. Use after each hosted research result to check relevance, source authority, freshness, layer coverage, and citation quality before accepting evidence.
---

# ReflectDeepSearchSkill

Judge whether a hosted DeepSearch result is good enough for evidence extraction.

## When To Use

Use this skill after a hosted provider returns a `DeepSearchResult`.

Do not use it to create new research tasks directly; `DecideResearchNextStepSkill` chooses the next action.

## Inputs

- `task: DeepSearchTask`
- `result: DeepSearchResult`

## Outputs

- `ReflectionResult`
- Schema export: `ReflectionResult` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Check relevance, source quality, freshness, layer coverage, and citation quality.
2. Require at least one P0/P1 source for source-quality success.
3. Require citations for factual claims; unsupported or inference claims reduce sufficiency.
4. Return missing evidence, weak sources, unsupported claims, and a follow-up question when result quality is insufficient.
5. Suggest the official-confirmation provider when official domains are required and the current provider failed to supply P0/P1 citations.

## Evidence And Failure Rules

- Do not mark a result enough when it lacks citations or source authority.
- Do not accept inference-only claims as factual evidence.
- Do not mutate evidence items in this skill.

## Acceptance Checks

- Output validates as `ReflectionResult`.
- `enough=True` only when all required quality gates pass.
- Output contains no final report markdown.
