# ESG Monthly Agent Project Structure

This file maps the project so a new reader can understand the flow without opening every module first.

## Core Entry Points

| Path | Purpose |
| --- | --- |
| `main.py` | CLI entry point. Builds input state, validates hosted provider configuration, runs the graph, and prints output paths. |
| `app.py` | LangGraph-compatible app export. Imports `build_graph()` and exposes `graph`. |
| `graph.py` | Main LangGraph orchestration. Connects pre-research, research, evidence extraction, reasoning, review, report, and export nodes. |
| `state.py` | Shared graph state contract. |
| `config.py` | Environment loading, provider defaults, source priority registry, default material ESG topics, and run path helpers. |

## Directories

| Path | Purpose |
| --- | --- |
| `agents/` | Helper modules for search planning, evidence repair, implementation help, and news research. |
| `nodes/` | LangGraph node functions. Each node adapts graph state to a skill runner or provider operation. |
| `subgraphs/` | Reusable LangGraph subgraphs for pre-research, DeepSearch, issue research, and targeted repair. |
| `skills/` | Stable single-purpose skill modules. Each skill has `SKILL.md`, `runner.py`, and `schema.py` where applicable. |
| `schemas/` | Pydantic schemas for evidence, sources, DeepSearch, events, issue chains, quality checks, recommendations, and reports. |
| `research_providers/` | Hosted and local research adapters: OpenAI, Anthropic, Qwen DashScope, Zhipu, Tavily, and local vector/manual-source mode. |
| `tools/` | Lower-level utilities for search, local sources, parsing, evidence storage, LLM review, and LangChain docs MCP access. |
| `prompts/` | Markdown prompt templates for extraction, mapping, quality review, and report writing. |
| `tests/` | Regression tests for graph state, providers, evidence extraction, report de-duplication, quality review, and CLI preflight. |
| `runs/` | Generated run artifacts. Keep `runs/.gitkeep`; do not ship generated run directories by default. |
| `storage/` | Local evidence/vector/raw/parsed storage. Keep `.gitkeep` placeholders; do not ship local DB or parsed artifacts by default. |
| `docs/` | Operational and structural documentation. |

For a maintainable-file inventory, see `docs/FILE_INVENTORY.md`.

## Pipeline

```text
main.py
  -> graph.py
  -> init_context
  -> pre_research_graph
  -> local research path or hosted DeepSearch path
  -> evidence extraction
  -> event classification
  -> issue chain builder
  -> company exposure
  -> benchmark-company comparison
  -> recommendation synthesis
  -> deterministic quality review
  -> optional targeted repair
  -> report writer
  -> optional LLM review
  -> export files
```

## Hosted Research Flow

```text
EvidenceNeed
  -> DeepSearchTask
  -> hosted provider
  -> DeepSearchResult with citations
  -> reflection / next-step decision
  -> EvidenceItem
  -> grouped event
  -> report event bullet
```

Current report de-duplication happens in two places:

- `skills/research_execution/evidence_from_deepsearch/runner.py`: citation-specific evidence text and quote extraction.
- `skills/common.py`: evidence grouping into event-level `RuleChange` / event records and report-level event rendering.

## What To Keep In A Clean Handoff

Keep:

- Source directories: `agents/`, `nodes/`, `subgraphs/`, `skills/`, `schemas/`, `research_providers/`, `tools/`, `prompts/`, `tests/`.
- Project files: `README.md`, `pyproject.toml`, `requirements-dev.txt`, `.env.example`, `.mcp.json`, `.gitignore`.
- Empty placeholders: `runs/.gitkeep`, `storage/chroma/.gitkeep`, `storage/raw/.gitkeep`, `storage/parsed/.gitkeep`.
- Documentation: `docs/RUNBOOK.md`, `docs/PROJECT_STRUCTURE.md`, `docs/FILE_INVENTORY.md`.

Exclude:

- `.env` and any `.env.*` file except `.env.example`.
- Generated run directories under `runs/`.
- `storage/evidence.sqlite` and local vector/raw/parsed artifacts.
- `__pycache__/`, `.pytest_cache/`, and `.DS_Store`.

## Verification Commands

```bash
cd /path/to/ESG-agent/esg_monthly_agent
LANGSMITH_TRACING=false pytest -q
python main.py --help
```

For a no-credential pipeline run, use the local deterministic command in `docs/RUNBOOK.md`.
