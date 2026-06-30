---
name: plan-deepsearch
description: Convert ESG evidence needs or SearchTask objects into DeepSearchTask objects for hosted web/deep research providers. Use before running hosted DeepSearch; do not use for URL fetching, browser scraping, PDF downloading, or local vector ingestion.
---

# PlanDeepSearchSkill

Create `DeepSearchTask` objects for hosted research providers.

## When To Use

Use this skill when an ESG monthly workflow needs to turn `EvidenceNeed`, `search_tasks`, or `repair_search_tasks` into hosted-search research tasks.

Do not use it for local file ingestion, MinerU parsing, Chroma/Milvus indexing, browser scraping, direct URL fetching, or PDF downloading.

## Inputs

- `state.search_tasks` or `state.repair_search_tasks`
- `state.company`
- `state.period`
- `state.max_search_calls_per_task`
- `state.max_research_rounds`

## Outputs

- `deepsearch_tasks: list[DeepSearchTask]`
- Schema export: `DeepSearchTask` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Output a hosted research goal and an initial question, not URLs or scraping instructions.
2. Preserve issue ID, layer, expected object type, company, period, source policy, queries, and freshness requirement.
3. Policy, standard, and rating layers should prefer regulators, exchanges, and rating providers.
4. Company layers should prefer company announcements, exchange filings, and company websites.
5. Benchmark-company (`peer`) layers should prefer benchmark-company annual reports, ESG reports, company websites, and exchange filings.
6. Always state whether freshness is required.

## Evidence And Failure Rules

- DeepSearch tasks are research instructions, not evidence.
- Do not invent provider results, citations, or source claims.
- If a repair task is present, prefer it over the original search task for the next hosted round.

## Acceptance Checks

- Output validates as `list[DeepSearchTask]`.
- Each task includes `must_search=True` and a bounded max-round/max-call policy.
- Output contains no final report markdown.
