---
name: search-task-planner
description: Create issue-aware SearchTask objects from evidence needs and source policy. Cover rule, industry, company, and benchmark-company layers.
---

# SearchTaskPlannerSkill

Creates executable search tasks for the evidence plan.

## When To Use

Runs after source registry and before query generation or DeepSearch planning.

Search execution, page fetching, and evidence extraction are outside this module.

## Inputs

- `state.evidence_needs`
- `state.source_registry`
- `state.company_profile`
- `state.period`
- `state.max_search_calls_per_task`

## Outputs

- `search_tasks: list[SearchTask]`
- Schema: `SearchTaskPlannerOutput`
- Runner: `runner.py`

## Execution Contract

1. Each task preserves issue, layer, source policy, and expected object type.
2. Task scope stays narrow enough to produce citable evidence.
3. Policy, company, and benchmark-company tasks prefer P0/P1 sources or configured official domains.
4. `peer` remains the internal enum for benchmark-company tasks.

## Evidence And Failure Rules

- Tasks and query hints are not evidence.
- Hosted web or DeepSearch modes do not plan direct scraping/fetching behavior.
- Authority or freshness uncertainty is encoded in inclusion criteria or missing-evidence expectations.

## Acceptance Checks

- Output validates as `list[SearchTask]`.
- Each task links to an issue and expected output schema.
- No report prose is emitted.
