# ESG Monthly Agent File Inventory

This inventory covers maintainable project files. Generated files under `runs/`, local storage artifacts under `storage/`, `.env`, caches, and OS metadata are excluded from the handoff set.

## Root Files

| File | Purpose |
| --- | --- |
| `README.md` | Project scope, run commands, provider notes, LangSmith, LLM review, and tests. |
| `main.py` | CLI entry point for report generation. |
| `app.py` | Exposes `graph` for LangGraph-compatible runtimes. |
| `graph.py` | Main graph composition and routing. |
| `state.py` | Typed graph state fields. |
| `config.py` | Environment loading, defaults, source priorities, material ESG topics, and output paths. |
| `pyproject.toml` | Python project metadata, dependency declarations, pytest config, and ruff line length. |
| `requirements-dev.txt` | Direct dependency install list for source-run and test environments. |
| `.env.example` | Safe environment template. |
| `.mcp.json` | LangChain docs MCP server configuration. |
| `.gitignore` | Keeps secrets, generated outputs, storage data, caches, and OS files out of the delivery set. |
| `__init__.py` | Marks `esg_monthly_agent` as an importable package when the parent directory is on `PYTHONPATH`. |

## Documentation

| File | Purpose |
| --- | --- |
| `docs/RUNBOOK.md` | Setup, smoke tests, local run, hosted run, optional LLM review, outputs, and failure modes. |
| `docs/PROJECT_STRUCTURE.md` | Directory map, pipeline map, hosted research flow, clean handoff rules, and verification commands. |
| `docs/FILE_INVENTORY.md` | This maintainable-file inventory. |

## Helper Modules

| File | Purpose |
| --- | --- |
| `agents/__init__.py` | Package marker. |
| `agents/news_research_agent.py` | High-level local search, parse, and evidence extraction helper. |
| `agents/search_planner_agent.py` | Search-task planning helper. |
| `agents/evidence_repair_agent.py` | Builds targeted repair tasks for missing evidence. |
| `agents/implementation_helper_agent.py` | LangChain docs helper for implementation checks. |

## Graph Nodes

| File | Purpose |
| --- | --- |
| `nodes/__init__.py` | Node package marker. |
| `nodes/init_context.py` | Initializes company, period, run paths, modes, and defaults. |
| `nodes/pre_research.py` | Runs pre-research skill steps. |
| `nodes/deepsearch.py` | Plans, executes, reflects, repairs, and extracts hosted DeepSearch evidence. |
| `nodes/execute_search.py` | Runs issue-aware local/generic search tasks. |
| `nodes/source_quality_filter.py` | Filters source candidates by source quality rules. |
| `nodes/fetch_pages.py` | Fetches pages only in local/fetch-allowed modes. |
| `nodes/parse_documents.py` | Parses fetched documents. |
| `nodes/extract_evidence.py` | Extracts EvidenceItem records from parsed documents. |
| `nodes/classify_events.py` | Groups evidence into rule, industry, company, and benchmark-company events. |
| `nodes/issue_chain_builder.py` | Builds issue chains from events. |
| `nodes/company_exposure.py` | Assesses company exposure. |
| `nodes/peer_benchmark.py` | Checks benchmark-company action signals. |
| `nodes/recommendation.py` | Synthesizes recommendations. |
| `nodes/quality_review.py` | Runs deterministic quality review and routes repair/pass. |
| `nodes/targeted_repair.py` | Generates repair tasks for quality gaps. |
| `nodes/report_writer.py` | Writes the structured markdown report. |
| `nodes/llm_review.py` | Runs optional OpenAI-compatible LLM report review. |
| `nodes/export_files.py` | Exports JSON artifacts and markdown reports. |

## Subgraphs

| File | Purpose |
| --- | --- |
| `subgraphs/__init__.py` | Subgraph package marker. |
| `subgraphs/pre_research_graph.py` | Pre-research graph composition. |
| `subgraphs/deepsearch_research_graph.py` | Hosted DeepSearch graph composition. |
| `subgraphs/issue_research_graph.py` | Local issue research graph composition. |
| `subgraphs/targeted_repair_graph.py` | Targeted repair graph composition. |

## Research Providers

| File | Purpose |
| --- | --- |
| `research_providers/__init__.py` | Provider registry exports. |
| `research_providers/base.py` | Provider protocol, errors, and helper types. |
| `research_providers/local_vector_provider.py` | Local/manual-source provider adapter. |
| `research_providers/openai_web_search_provider.py` | OpenAI hosted web-search adapter and shared citation/source helpers. |
| `research_providers/openai_deep_research_provider.py` | OpenAI deep-research provider wrapper. |
| `research_providers/anthropic_web_search_provider.py` | Anthropic server-side web-search adapter. |
| `research_providers/qwen_dashscope_search_provider.py` | Qwen DashScope search-enabled generation adapter. |
| `research_providers/zhipu_web_search_provider.py` | Zhipu official Web Search and GLM OpenAI-compatible gateway adapter. |
| `research_providers/tavily_official_search_provider.py` | Tavily official-domain search adapter with generic list-page filtering. |

## Schemas

| File | Purpose |
| --- | --- |
| `schemas/__init__.py` | Schema package marker. |
| `schemas/base.py` | Shared schema base helpers. |
| `schemas/company.py` | Company profile and boundary schemas. |
| `schemas/source.py` | Source record schemas. |
| `schemas/evidence.py` | Evidence item schema. |
| `schemas/deepsearch.py` | DeepSearch task, citation, result, reflection, and decision schemas. |
| `schemas/rule_change.py` | Rule-change schema. |
| `schemas/event.py` | Industry, company, and benchmark-company event schemas. |
| `schemas/issue.py` | Material issue and issue-chain schemas. |
| `schemas/exposure.py` | Company exposure assessment schema. |
| `schemas/peer_action.py` | Benchmark-company action schema. |
| `schemas/recommendation.py` | Recommendation schema. |
| `schemas/quality.py` | Quality-review schema. |
| `schemas/report.py` | Report schema. |

## Skill Modules

Each skill directory contains `SKILL.md` for the contract, `runner.py` for execution, and `schema.py` for local input/output types when needed.

| Skill directory | Purpose |
| --- | --- |
| `skills/pre_research/company_boundary/` | Defines company scope, tickers, and benchmark-company boundary context. |
| `skills/pre_research/customer_segment/` | Maps business segments. The directory name is retained for compatibility. |
| `skills/pre_research/materiality_issue/` | Builds material ESG issues. |
| `skills/pre_research/source_registry/` | Builds source registry and priority hints. |
| `skills/pre_research/evidence_need_builder/` | Converts issues into evidence needs. |
| `skills/pre_research/query_generation/` | Generates issue-aware queries. |
| `skills/pre_research/search_task_planner/` | Plans local search tasks. |
| `skills/pre_research/report_contract/` | Builds the report contract. |
| `skills/deepsearch/plan_deepsearch/` | Converts evidence needs into hosted DeepSearch tasks. |
| `skills/deepsearch/reflect_deepsearch/` | Reviews DeepSearch result quality and gaps. |
| `skills/deepsearch/decide_research_next_step/` | Decides whether to retry, switch provider, or accept evidence. |
| `skills/research_execution/search_executor/` | Executes local/generic search tasks. |
| `skills/research_execution/source_quality_filter/` | Applies source-quality filtering. |
| `skills/research_execution/fetch_and_parse/` | Fetches and parses local/fetch-allowed source content. |
| `skills/research_execution/evidence_extraction/` | Extracts evidence from parsed local documents. |
| `skills/research_execution/evidence_from_deepsearch/` | Converts DeepSearch citations into evidence items. |
| `skills/reasoning/event_classification/` | Classifies evidence into event families. |
| `skills/reasoning/issue_chain_builder/` | Builds issue chains. |
| `skills/reasoning/company_exposure/` | Assesses report-subject exposure. |
| `skills/reasoning/peer_benchmark/` | Checks benchmark-company actions. |
| `skills/reasoning/recommendation/` | Builds recommendation records. |
| `skills/reasoning/quality_review/` | Runs deterministic quality checks. |
| `skills/reasoning/report_writer/` | Renders report markdown. |
| `skills/common.py` | Shared deterministic logic used by many skill runners. |
| `skills/__init__.py` and subgroup `__init__.py` files | Package markers and module grouping. |

## Tools

| File | Purpose |
| --- | --- |
| `tools/__init__.py` | Tool package marker. |
| `tools/web_search.py` | Generic search tool wrapper. |
| `tools/news_search.py` | News-search wrapper. |
| `tools/fetcher.py` | HTTP fetch utility for local/fetch-allowed paths. |
| `tools/html_parser.py` | HTML parsing utility. |
| `tools/pdf_parser.py` | PDF parsing utility. |
| `tools/local_sources.py` | Local/manual source loader. |
| `tools/source_ranker.py` | Source quality ranking helper. |
| `tools/evidence_store.py` | SQLite evidence store helper. |
| `tools/chroma_store.py` | Local Chroma vector store helper. |
| `tools/llm_client.py` | OpenAI-compatible LLM client and config builder. |
| `tools/docs_mcp.py` | LangChain docs MCP helper. |

## Prompts

| File | Purpose |
| --- | --- |
| `prompts/extract_rule_changes.md` | Prompt template for rule changes. |
| `prompts/extract_industry_event.md` | Prompt template for industry events. |
| `prompts/extract_company_event.md` | Prompt template for company events. |
| `prompts/extract_peer_action.md` | Prompt template for benchmark-company actions. |
| `prompts/map_rule_to_issue.md` | Prompt template for rule-to-issue mapping. |
| `prompts/assess_company_exposure.md` | Prompt template for exposure assessment. |
| `prompts/synthesize_recommendation.md` | Prompt template for recommendations. |
| `prompts/quality_review.md` | Prompt template for quality review. |
| `prompts/write_report.md` | Prompt template for report writing. |

## Tests

| File | Purpose |
| --- | --- |
| `tests/__init__.py` | Test package marker. |
| `tests/test_state.py` | State shape tests. |
| `tests/test_schemas.py` | Schema validation tests. |
| `tests/test_graph_smoke.py` | Graph smoke tests. |
| `tests/test_agents.py` | Agent helper tests. |
| `tests/test_cli_preflight.py` | Hosted provider preflight tests. |
| `tests/test_deepsearch_provider_interface.py` | Provider adapter tests. |
| `tests/test_call_all_available_providers.py` | Provider fan-out tests. |
| `tests/test_no_fetch_in_hosted_web_mode.py` | Hosted mode no-fetch regression tests. |
| `tests/test_source_mode_blocks_fetch.py` | Source-mode fetch blocking tests. |
| `tests/test_reflect_decide_loop.py` | DeepSearch reflection/decision loop tests. |
| `tests/test_extract_evidence_from_deepsearch.py` | DeepSearch citation-to-evidence tests. |
| `tests/test_report_deduplication.py` | Report event de-duplication regression tests. |
| `tests/test_issue_chain_builder.py` | Issue-chain builder tests. |
| `tests/test_quality_review.py` | Quality-review tests. |
| `tests/test_llm_client.py` | LLM client configuration tests. |

## Placeholders Kept For Directory Shape

| File | Purpose |
| --- | --- |
| `runs/.gitkeep` | Preserves the generated-run directory in a clean checkout. |
| `storage/chroma/.gitkeep` | Preserves local vector storage directory. |
| `storage/raw/.gitkeep` | Preserves raw local source storage directory. |
| `storage/parsed/.gitkeep` | Preserves parsed local source storage directory. |
