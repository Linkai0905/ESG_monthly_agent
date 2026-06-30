<div align="center">
  <h1>ESG Monthly Agent</h1>
  <h3>基于 LangGraph 的 ESG 月报检索、证据组织与草稿生成流程</h3>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue" alt="Python 3.11">
  <img src="https://img.shields.io/badge/LangGraph-workflow-green" alt="LangGraph">
  <img src="https://img.shields.io/badge/Pydantic-schema-orange" alt="Pydantic">
  <img src="https://img.shields.io/badge/Output-Markdown-lightgrey" alt="Markdown">
</div>

<br>

`esg_monthly_agent` 是一个 ESG 月报生成原型。当前版本以中国神华为默认案例，把 ESG 政策、行业动态、公司事件、对标企业行动和管理建议组织成带证据引用的月报草稿。

项目包含两类资料路径：本地资料路径用于离线调试和固定语料回归，hosted web 路径用于调用 Tavily、智谱、DashScope、OpenAI 或 Anthropic 等带检索能力的服务。系统会把中间结果写入 `runs/`，包括检索任务、证据条目、议题链、建议、质量检查和最终 Markdown 报告。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

```bash
python main.py --company 中国神华 --period 2026-06 \
  --tickers 601088.SH 01088.HK \
  --peers 中煤能源 陕西煤业 兖矿能源 华能国际 华电国际
```

> 生成结果是月报草稿，不替代公司内部数据核验、ESG 专业判断或合规审阅。

## Scope

本项目当前解决的是“把 ESG 月报资料整理成可追溯草稿”的工程问题，重点包括：

- **证据组织**：将政策、行业、公司和对标企业资料整理成 `EvidenceItem`，并保留来源、日期、引用和任务信息。
- **议题链构建**：围绕安全生产、气候变化、污染物管理、公司治理等 ESG 议题，把规则、行业信号、公司暴露和建议串联起来。
- **报告生成**：根据结构化状态生成 Markdown 月报，事实性内容尽量关联 evidence id。
- **质量检查**：在导出前检查证据缺口、来源等级、引用覆盖、建议依据和样例来源风险。
- **运行留痕**：每次运行都会导出 JSON 中间结果，便于定位是检索、证据抽取、分类还是报告写作阶段的问题。

当前版本仍是 MVP / demo 形态。它提供可运行的流程和测试用例，但不声称完全替代分析师，也不保证外部检索结果覆盖所有重要信息。

## Architecture

### Workflow

```text
company / period / tickers / benchmark companies
        ↓
report_contract
        ↓
company_boundary / business_segment / materiality_issue
        ↓
evidence_need_builder
        ↓
local source path or hosted DeepSearch path
        ↓
EvidenceItem[]
        ↓
event_classification
        ↓
issue_chain_builder
        ↓
company_exposure
        ↓
benchmark-company comparison
        ↓
recommendation
        ↓
quality_review
        ↓
report_writer
        ↓
reports/esg_monthly_report.md
```

### LangGraph Nodes

`graph.py` 编排完整流程，节点主要做状态转换和模块调用：

```text
init_context
  ↓
pre_research_graph
  ↓
local research path / hosted DeepSearch path
  ↓
extract_evidence
  ↓
classify_events
  ↓
issue_chain_builder
  ↓
company_exposure
  ↓
peer_benchmark
  ↓
recommendation
  ↓
quality_review
  ↓
targeted_repair (optional)
  ↓
report_writer
  ↓
llm_review (optional)
  ↓
export_files
```

关键约束：

- hosted web / deep research 模式不直接抓取网页正文；实时资料由对应 provider 返回引用和片段。
- `report_writer` 只消费结构化状态，不新增事实。
- P2/P3 来源可以作为线索，但不能单独支撑事实性结论。
- `.env`、`runs/`、本地存储和缓存不应作为公开交付内容提交。

### Hosted Research Loop

```text
EvidenceNeed
  ↓
PlanDeepSearchSkill
  ↓
DeepSearchTask
  ↓
hosted research provider
  ↓
DeepSearchResult with citations
  ↓
ReflectDeepSearchSkill
  ↓
DecideResearchNextStepSkill
  ↓
EvidenceFromDeepSearchSkill
  ↓
EvidenceItem
```

当任务要求官方域名但当前 provider 没有返回 P0/P1 引用时，反思节点会记录缺口，并可触发 provider 切换或后续修复任务。

## Project Structure

```text
.
├── main.py                         # 命令行入口
├── app.py                          # LangGraph 兼容入口，导出 graph
├── graph.py                        # LangGraph 主流程
├── state.py                        # 图状态定义
├── config.py                       # 环境变量、默认配置、输出路径
├── pyproject.toml                  # Python 项目配置
├── requirements-dev.txt            # 运行与测试依赖
├── .env.example                    # 环境变量模板
├── .mcp.json                       # LangChain docs MCP 配置
├── agents/                         # 搜索规划、证据修复等辅助模块
├── nodes/                          # LangGraph 节点函数
├── subgraphs/                      # 预研、检索、修复等子图
├── skills/                         # 单一职责 skill 契约、runner 和 schema
├── schemas/                        # Pydantic 数据结构
├── research_providers/             # hosted / local research provider 适配器
├── tools/                          # 本地资料、解析、证据库、LLM review 等工具
├── prompts/                        # 提取、评估、报告写作 prompt 模板
├── tests/                          # 回归测试
├── docs/                           # 运行手册、结构说明、文件清单
├── runs/                           # 运行输出目录，默认只保留 .gitkeep
└── storage/                        # 本地证据和向量存储占位目录
```

更细的文件清单见 `docs/FILE_INVENTORY.md`。

## Quickstart

### 1. Create Environment

建议使用 Python 3.11。

```bash
cd /path/to/ESG-agent/esg_monthly_agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

也可以用 `pyproject.toml` 安装：

```bash
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

复制环境变量模板：

```bash
cp .env.example .env
```

本地调试可以保留默认的 local source / seed evidence 配置。正式跑外部检索时，至少需要关闭本地 fallback，并填写对应 provider key：

```bash
ESG_USE_LOCAL_SOURCES=false
ESG_USE_SEED_EVIDENCE=false
ESG_RESEARCH_MODE=hosted_web
ESG_DEFAULT_RESEARCH_PROVIDER=tavily_official_search
TAVILY_API_KEY=your_tavily_key
```

常用 provider 环境变量：

| Provider | Required key | Notes |
|---|---|---|
| `tavily_official_search` | `TAVILY_API_KEY` | 使用 Tavily Search，并按任务 `allowed_domains` 限定域名 |
| `zhipu_web_search` | `ZHIPU_API_KEY` 或 `BIGMODEL_API_KEY` | 使用智谱官方 Web Search API |
| `qwen_dashscope_search` | `DASHSCOPE_API_KEY` 或 `QWEN_DASHSCOPE_API_KEY` | 使用 DashScope search-enabled generation |
| `openai_web_search` | `OPENAI_API_KEY` | 使用 OpenAI Responses API 的 hosted web search |
| `anthropic_web_search` | `ANTHROPIC_API_KEY` | 使用 Claude server-side web search |

### 3. Run Local Pipeline

本地模式适合检查流程、schema 和报告写作：

```bash
python main.py --company 中国神华 --period 2026-06 \
  --tickers 601088.SH 01088.HK \
  --peers 中煤能源 陕西煤业 兖矿能源 华能国际 华电国际
```

### 4. Run Hosted Web Research

示例：使用 Tavily 跑 hosted web 路径。

```bash
ESG_USE_LOCAL_SOURCES=false \
ESG_USE_SEED_EVIDENCE=false \
python main.py \
  --company 中国神华 \
  --period 2026-06 \
  --research-mode hosted_web \
  --research-provider tavily_official_search \
  --max-research-rounds 2 \
  --max-search-calls 2
```

如果需要第一轮同时尝试所有已配置 provider：

```bash
python main.py \
  --company 中国神华 \
  --period 2026-06 \
  --research-mode hosted_web \
  --call-all-available-providers
```

未配置 key 的 provider 会被可用性检查跳过。hosted 模式缺少必要 key 时，CLI 会在生成报告前退出。

## Outputs

默认输出目录为：

```text
runs/{period}_{company}/
```

核心输出文件：

| File | Description |
|---|---|
| `reports/esg_monthly_report.md` | ESG 月报草稿 |
| `reports/report_final.md` | 当前最终报告文件 |
| `evidence_items.json` | 结构化证据条目 |
| `source_records.json` | 来源记录 |
| `deepsearch_tasks.json` | hosted research 任务 |
| `deepsearch_results.json` | provider 返回结果和引用 |
| `deepsearch_decisions.json` | 反思和下一步决策 |
| `rule_changes.json` | 政策、评级、标准相关事件 |
| `industry_events.json` | 行业事件 |
| `company_events.json` | 公司事件 |
| `peer_actions.json` | 对标企业行动，字段名沿用内部 schema |
| `issue_chains.json` | ESG 议题链 |
| `company_exposures.json` | 公司暴露评估 |
| `recommendations.json` | 管理建议 |
| `quality_checks.json` | 质量检查结果 |

报告中出现的事实性判断应能回到 `evidence_items.json` 或对应 hosted research 结果中查看来源。

## LangSmith

项目会在构建图之前读取 `.env`。如需记录 LangSmith trace，填写：

```bash
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=ESG-month-report
LANGSMITH_API_KEY=your_langsmith_key
```

如果没有配置 `LANGSMITH_API_KEY`，建议显式关闭：

```bash
LANGSMITH_TRACING=false
```

## Optional LLM Review

报告生成后可以调用 OpenAI-compatible Chat Completions API 做独立 review，输出到 `llm_review.json`。该步骤不会覆盖 Markdown 报告。

```bash
export ESG_LLM_API_KEY=your_llm_key
python main.py --company 中国神华 --period 2026-06 \
  --use-llm \
  --llm-provider deepseek \
  --llm-model deepseek-v4-pro \
  --llm-base-url https://api.deepseek.com
```

Chat-only 网关只用于可选 review，不能替代 hosted web search。只有 provider 返回可映射来源 URL 时，才可能进入证据链。

## Tests

```bash
LANGSMITH_TRACING=false pytest -q
```

当前测试覆盖 schema、graph smoke、provider preflight、hosted 模式 fetch 禁用、DeepSearch 反思决策、证据抽取、报告去重、质量检查和 LLM client 配置。

## Notes

- 当前默认报告对象是中国神华，CLI 仍支持传入其他公司名称，但行业议题、对标企业和报告口径需要按实际场景复核。
- 外部检索质量取决于 provider 返回结果、关键词、日期范围和官方域名覆盖情况。
- P2/P3 或媒体来源可以保留为线索，但正式报告中不应单独作为关键事实依据。
- `.env`、API key、`runs/` 输出、`storage/` 数据库和缓存文件不应提交到公开仓库。
- 本仓库未指定开源许可证；公开分发前需要补充或确认 License。
