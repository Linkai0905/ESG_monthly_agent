---
name: query-generation
description: Generate query variants from planned ESG SearchTask objects for local search, Tavily, Zhipu, or hosted search providers.
---

# QueryGenerationSkill

Generates search expressions around issue, layer, company, and period.

## When To Use

Runs after search task planning and before search execution or DeepSearch task construction.

Evidence sufficiency decisions and conclusions are outside this module.

## Inputs

- `state.search_tasks`
- `state.company_profile`
- `state.period`
- `state.source_registry`

## Outputs

- `generated_queries: list[dict]`
- Schema: `QueryGenerationOutput`
- Runner: `runner.py`

## Execution Contract

1. Queries preserve issue, layer, report subject, benchmark companies, and period.
2. Official-source hints are included when source policy requires them.
3. Query text stays short, specific, and executable.
4. Queries do not broaden into topics that cannot be attributed back to a task.

## Evidence And Failure Rules

- Query text is not evidence.
- Facts, URLs, and source titles are not invented.
- Incomplete context produces a minimal valid query object and leaves gaps for execution and quality checks.

## Acceptance Checks

- Output validates as `list[dict]`.
- Each query traces to a task or issue.
- No recommendation or report prose is emitted.
