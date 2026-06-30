# ESG Monthly Agent Runbook

This guide describes how to install dependencies, run the pipeline, inspect outputs, and handle the most common failure modes.

## 1. Environment

Use Python 3.11 or newer.

```bash
cd /path/to/ESG-agent/esg_monthly_agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Keep `.env` private. Only `.env.example` should be shared as a template.

The source tree is designed to run directly from `esg_monthly_agent/`. `main.py` adds the parent directory to `sys.path` when launched as a script, and the pytest configuration also sets `pythonpath = [".."]`.

## 2. Smoke Test

Run the test suite first:

```bash
LANGSMITH_TRACING=false pytest -q
```

Use the pytest summary as the result for the local checkout. A passing run should end with a `passed` summary, for example:

```text
48 passed
```

## 3. Local Deterministic Run

This path does not require hosted web-search credentials. It uses local or manually supplied sources when present. Seed evidence is a development fallback and should stay disabled for live evidence runs.

```bash
LANGSMITH_TRACING=false \
ESG_OUTPUT_DIR=runs/local_smoke \
ESG_USE_LOCAL_SOURCES=true \
ESG_USE_SEED_EVIDENCE=true \
python main.py \
  --company 中国神华 \
  --period 2026-06 \
  --research-mode local_vector \
  --research-provider local_vector \
  --tickers 601088.SH 01088.HK \
  --peers 中煤能源 陕西煤业 兖矿能源 华能国际 华电国际
```

The command prints the run id, report path, and quality result.
The explicit `--research-mode local_vector` and `--research-provider local_vector` flags keep this smoke run local even if `.env` is configured for hosted web research.

## 4. Hosted Web Run

Hosted mode requires valid provider keys in `.env`. Configure only the providers that should be available.

For a GLM OpenAI-compatible gateway used by the Zhipu provider, set:

```bash
ZHIPU_WEB_SEARCH_API_URL=https://your-gateway.example/v1
ZHIPU_WEB_SEARCH_MODEL=glm-5.2
ZHIPU_API_KEY=your_provider_key
```

For Tavily, set:

```bash
TAVILY_API_KEY=your_tavily_key
```

Then run:

```bash
LANGSMITH_TRACING=false \
ESG_OUTPUT_DIR=runs/live_all_available \
ESG_USE_LOCAL_SOURCES=false \
ESG_USE_SEED_EVIDENCE=false \
ESG_DEEPSEARCH_CONCURRENCY=3 \
python main.py \
  --company 中国神华 \
  --period 2026-06 \
  --research-mode hosted_web \
  --research-provider zhipu_web_search \
  --call-all-available-providers \
  --max-research-rounds 3 \
  --max-search-calls 3
```

`--call-all-available-providers` runs the first hosted research round against each configured provider that has code support and credentials. Providers without keys are skipped by availability checks.

## 5. Optional LLM Review

The LLM reviewer is separate from evidence collection. It writes `llm_review.json` and does not overwrite the report.

```bash
ESG_LLM_API_KEY=your_llm_gateway_key \
python main.py \
  --company 中国神华 \
  --period 2026-06 \
  --use-llm \
  --llm-provider glm-compatible \
  --llm-model glm-5.2 \
  --llm-base-url https://your-gateway.example/v1
```

## 6. Outputs

By default, each run writes to:

```text
runs/{period}_{company}/
```

If `ESG_OUTPUT_DIR=runs/local_smoke`, the same run writes to `runs/local_smoke/{period}_{company}/`.

Key artifacts:

- `reports/esg_monthly_report.md`: primary markdown report.
- `reports/report_final.md`: final report alias for downstream use.
- `evidence_items.json`: normalized evidence items with source metadata.
- `deepsearch_tasks.json`: planned research tasks.
- `deepsearch_results.json`: provider results, citations, and provider errors.
- `deepsearch_reflections.json`: quality/reflection decisions per task.
- `issue_chains.json`: issue-level reasoning chains.
- `recommendations.json`: final recommendations.
- `quality_checks.json`: deterministic quality gate.
- `llm_review.json`: optional LLM review artifact.

`Quality passed: False` does not mean the pipeline crashed. It means the deterministic quality gate found gaps such as missing official links, weak recommendations, or uncovered issue areas.

## 7. Common Failure Modes

- `HTTP 401 Invalid token`: the provider key is invalid, expired, or not accepted by the configured gateway URL.
- Tavily `HTTP 432`: the plan or usage quota is exceeded.
- `no allowed-domain P0/P1 URL citations`: the provider returned content, but no citation matched the task's official-domain allowlist.
- LangSmith 401 noise: set `LANGSMITH_TRACING=false` or provide `LANGSMITH_API_KEY`.
- Empty hosted report: make sure `ESG_USE_SEED_EVIDENCE=false` is intentional and at least one hosted provider has valid credentials.

## 8. Delivery Check

Before sharing the project:

```bash
LANGSMITH_TRACING=false pytest -q
python main.py --help
```

Do not include `.env`, generated `runs/*`, SQLite stores, local Chroma data, `__pycache__`, `.pytest_cache`, or `.DS_Store` files.
