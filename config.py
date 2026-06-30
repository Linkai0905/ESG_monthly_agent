from __future__ import annotations

import os
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_local_env()
if os.getenv("LANGSMITH_TRACING", "").lower() in {"1", "true", "yes"} and not os.getenv(
    "LANGSMITH_API_KEY"
):
    os.environ["LANGSMITH_TRACING"] = "false"

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / os.getenv("ESG_OUTPUT_DIR", "runs")
USE_SEED_EVIDENCE = os.getenv("ESG_USE_SEED_EVIDENCE", "true").lower() in {
    "1",
    "true",
    "yes",
}
USE_LOCAL_SOURCES = os.getenv("ESG_USE_LOCAL_SOURCES", "true").lower() in {
    "1",
    "true",
    "yes",
}
USE_LLM_REVIEW = os.getenv("ESG_USE_LLM", os.getenv("ESG_USE_QWEN", "false")).lower() in {
    "1",
    "true",
    "yes",
}
LLM_PROVIDER = os.getenv("ESG_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "deepseek"))
LLM_BASE_URL = os.getenv(
    "ESG_LLM_BASE_URL",
    os.getenv(
        "LLM_BASE_URL",
        os.getenv("QWEN_BASE_URL", os.getenv("DASHSCOPE_BASE_URL", "https://api.deepseek.com")),
    ),
)
LLM_MODEL = os.getenv(
    "ESG_LLM_MODEL",
    os.getenv("LLM_MODEL", os.getenv("QWEN_MODEL", os.getenv("DASHSCOPE_MODEL", "deepseek-v4-pro"))),
)
LLM_TIMEOUT_SECONDS = int(os.getenv("ESG_LLM_TIMEOUT_SECONDS", os.getenv("QWEN_TIMEOUT_SECONDS", "60")))
LLM_MAX_TOKENS = int(os.getenv("ESG_LLM_MAX_TOKENS", os.getenv("QWEN_MAX_TOKENS", "1200")))

RESEARCH_MODE = os.getenv("ESG_RESEARCH_MODE", "local_vector")
DEFAULT_RESEARCH_PROVIDER = os.getenv("ESG_DEFAULT_RESEARCH_PROVIDER", "openai_web_search")
ENABLED_RESEARCH_PROVIDERS = [
    item.strip()
    for item in os.getenv(
        "ESG_ENABLED_RESEARCH_PROVIDERS",
        "openai_web_search,openai_deep_research,anthropic_web_search,qwen_dashscope_search,zhipu_web_search,zhipu_glm_web_search,tavily_official_search,local_vector",
    ).split(",")
    if item.strip()
]
MAX_RESEARCH_ROUNDS = int(os.getenv("ESG_MAX_RESEARCH_ROUNDS", "3"))
MAX_SEARCH_CALLS_PER_TASK = int(os.getenv("ESG_MAX_SEARCH_CALLS_PER_TASK", "8"))
CALL_ALL_AVAILABLE_PROVIDERS = os.getenv("ESG_CALL_ALL_AVAILABLE_PROVIDERS", "false").lower() in {
    "1",
    "true",
    "yes",
}
REQUIRE_HOSTED_SEARCH_FOR_WEB = os.getenv("ESG_REQUIRE_HOSTED_SEARCH_FOR_WEB", "true").lower() in {
    "1",
    "true",
    "yes",
}
ALLOW_FETCH_IN_WEB_MODE = os.getenv("ESG_ALLOW_FETCH_IN_WEB_MODE", "false").lower() in {
    "1",
    "true",
    "yes",
}
OPENAI_WEB_SEARCH_MODEL = os.getenv("OPENAI_WEB_SEARCH_MODEL", "gpt-5.5")
OPENAI_DEEP_RESEARCH_MODEL = os.getenv("OPENAI_DEEP_RESEARCH_MODEL", "o3-deep-research")
ANTHROPIC_WEB_SEARCH_MODEL = os.getenv("ANTHROPIC_WEB_SEARCH_MODEL", "claude-opus-4-8")
ANTHROPIC_WEB_SEARCH_TOOL_TYPE = os.getenv("ANTHROPIC_WEB_SEARCH_TOOL_TYPE", "web_search_20260318")
ZHIPU_WEB_SEARCH_API_URL = os.getenv(
    "ZHIPU_WEB_SEARCH_API_URL",
    "https://open.bigmodel.cn/api/paas/v4/web_search",
)
ZHIPU_WEB_SEARCH_MODEL = os.getenv("ZHIPU_WEB_SEARCH_MODEL", os.getenv("ESG_LLM_MODEL", "glm-5.2"))
ZHIPU_WEB_SEARCH_ENGINE = os.getenv("ZHIPU_WEB_SEARCH_ENGINE", "search_pro")
ZHIPU_WEB_SEARCH_COUNT = int(os.getenv("ZHIPU_WEB_SEARCH_COUNT", "10"))
ZHIPU_WEB_SEARCH_CONTENT_SIZE = os.getenv("ZHIPU_WEB_SEARCH_CONTENT_SIZE", "high")
ZHIPU_WEB_SEARCH_RECENCY = os.getenv("ZHIPU_WEB_SEARCH_RECENCY", "noLimit")
TAVILY_SEARCH_API_URL = os.getenv("TAVILY_SEARCH_API_URL", "https://api.tavily.com/search")
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "advanced")
TAVILY_SEARCH_MAX_RESULTS = int(os.getenv("TAVILY_SEARCH_MAX_RESULTS", "5"))
QWEN_DASHSCOPE_SEARCH_MODEL = os.getenv("QWEN_DASHSCOPE_SEARCH_MODEL", os.getenv("QWEN_MODEL", "qwen-plus"))
QWEN_DASHSCOPE_WORKSPACE_ID = os.getenv("QWEN_DASHSCOPE_WORKSPACE_ID", "").strip()
QWEN_DASHSCOPE_REGION = os.getenv("QWEN_DASHSCOPE_REGION", "cn-beijing").strip() or "cn-beijing"
QWEN_DASHSCOPE_SEARCH_STRATEGY = os.getenv("QWEN_DASHSCOPE_SEARCH_STRATEGY", "turbo").strip()


def _qwen_dashscope_api_url() -> str:
    explicit = os.getenv("QWEN_DASHSCOPE_API_URL", "").strip()
    if explicit:
        return explicit
    if QWEN_DASHSCOPE_WORKSPACE_ID:
        return (
            f"https://{QWEN_DASHSCOPE_WORKSPACE_ID}.{QWEN_DASHSCOPE_REGION}.maas.aliyuncs.com"
            "/api/v1/services/aigc/text-generation/generation"
        )
    return "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


QWEN_DASHSCOPE_API_URL = _qwen_dashscope_api_url()
OPENAI_RESPONSES_BASE_URL = os.getenv("OPENAI_RESPONSES_BASE_URL", "https://api.openai.com/v1")
ANTHROPIC_API_BASE_URL = os.getenv("ANTHROPIC_API_BASE_URL", "https://api.anthropic.com/v1")
OPENAI_DEEP_RESEARCH_ENABLED = os.getenv("OPENAI_DEEP_RESEARCH_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}
OPENAI_ALLOW_UNLIMITED_DEEP_RESEARCH_TOKENS = os.getenv(
    "OPENAI_ALLOW_UNLIMITED_DEEP_RESEARCH_TOKENS", "false"
).lower() in {"1", "true", "yes"}
OPENAI_BACKGROUND_RESEARCH = os.getenv("OPENAI_BACKGROUND_RESEARCH", "false").lower() in {
    "1",
    "true",
    "yes",
}
DEFAULT_LOCAL_SOURCE_DIR = Path(
    os.getenv("ESG_LOCAL_SOURCE_DIR", str(PROJECT_ROOT.parent / "ESG-RAG" / "data" / "manual_sources"))
)
DEFAULT_MANUAL_SOURCE_CSV = Path(
    os.getenv("ESG_MANUAL_SOURCE_CSV", str(PROJECT_ROOT.parent / "ESG-RAG" / "manual_sources.csv"))
)

DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_REPORT_TYPE = "monthly"


def parse_period(period: str | None) -> dict[str, str]:
    if not period:
        today = date.today()
        return _month_period(today.year, today.month)

    cleaned = period.strip().replace("至", " ").replace("~", " ").replace("—", " ")
    parts = [part for part in cleaned.split() if part]
    if len(parts) >= 2 and len(parts[0]) >= 10 and len(parts[1]) >= 10:
        return {"start": parts[0][:10], "end": parts[1][:10], "label": parts[0][:7]}

    if len(cleaned) == 7 and cleaned[4] == "-":
        year, month = cleaned.split("-")
        return _month_period(int(year), int(month))

    if len(cleaned) >= 10:
        start = date.fromisoformat(cleaned[:10])
        return _month_period(start.year, start.month)

    raise ValueError(f"Unsupported period format: {period}")


def _month_period(year: int, month: int) -> dict[str, str]:
    last_day = monthrange(year, month)[1]
    return {
        "start": f"{year:04d}-{month:02d}-01",
        "end": f"{year:04d}-{month:02d}-{last_day:02d}",
        "label": f"{year:04d}-{month:02d}",
    }


def make_run_id(company: str, period: dict[str, str]) -> str:
    safe_company = company.replace("/", "_").replace(" ", "")
    return f"{period['label']}_{safe_company}"


def build_run_paths(run_id: str) -> dict[str, Path]:
    base = DEFAULT_OUTPUT_DIR / run_id
    paths = {
        "base": base,
        "reports": base / "reports",
        "raw": base / "raw",
        "parsed": base / "parsed",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


SOURCE_PRIORITY_REGISTRY: list[dict[str, Any]] = [
    {
        "priority": "P0",
        "authority_score": 1.0,
        "sources": [
            "公司官网",
            "交易所公告",
            "年报 / ESG报告 / 可持续发展报告",
            "国家发改委",
            "国家能源局",
            "生态环境部",
            "应急管理部",
            "国家矿山安全监察局",
            "上交所 / 港交所",
            "ISSB / IFRS",
            "MSCI / Sustainalytics / CDP 官方方法文件",
        ],
        "rules": [
            "高风险 ESG 判断不能只由 P2 / P3 来源支撑。",
            "公司事件必须优先使用公司公告、交易所公告、官网。",
            "政策 / 标准 / 评级变化必须优先使用监管机构、交易所、评级机构官方文件。",
        ],
    },
    {
        "priority": "P1",
        "authority_score": 0.8,
        "sources": ["新华社", "央视网", "央企官网", "行业协会", "权威财经媒体", "主流证券媒体"],
        "rules": ["可作为行业动态和最佳实践的辅助支撑。"],
    },
    {
        "priority": "P2",
        "authority_score": 0.55,
        "sources": ["券商研报", "第三方 ESG 数据机构", "行业研究平台"],
        "rules": ["仅作为分析补充，不单独支撑高风险结论。"],
    },
    {
        "priority": "P3",
        "authority_score": 0.2,
        "sources": ["自媒体", "论坛", "无来源转载", "内容农场"],
        "rules": ["仅作线索，不直接支撑高风险结论。"],
    },
]


DEFAULT_MATERIALITY_TOPICS: list[dict[str, Any]] = [
    {
        "issue_id": "climate_transition",
        "issue_name": "气候变化与能源转型",
        "description": "煤炭与电力组合在双碳目标、碳市场和转型金融下的长期暴露。",
        "esg_dimensions": ["E", "G"],
        "materiality_level": "high",
        "related_segments": ["煤炭生产", "煤电运营", "煤炭销售"],
        "keywords": ["气候变化", "能源转型", "双碳", "碳市场", "转型金融"],
    },
    {
        "issue_id": "coal_power_decarbonization",
        "issue_name": "煤电节能降碳与灵活性改造",
        "description": "煤电机组节能降耗、供热改造、灵活性调节与低碳技术改造。",
        "esg_dimensions": ["E"],
        "materiality_level": "high",
        "related_segments": ["发电", "煤电一体化"],
        "keywords": ["煤电", "节能降碳", "灵活性改造", "能效", "供电煤耗"],
    },
    {
        "issue_id": "mine_safety",
        "issue_name": "煤矿安全生产与职业健康",
        "description": "矿山安全监管、智能矿山、承包商安全和职业健康。",
        "esg_dimensions": ["S", "G"],
        "materiality_level": "high",
        "related_segments": ["煤炭生产", "矿山运营"],
        "keywords": ["煤矿安全", "安全生产", "职业健康", "智能矿山", "隐患整改"],
    },
    {
        "issue_id": "green_mine_ecology",
        "issue_name": "绿色矿山与生态修复",
        "description": "绿色矿山建设、土地复垦、水土保持、生物多样性与生态修复。",
        "esg_dimensions": ["E"],
        "materiality_level": "high",
        "related_segments": ["煤炭生产", "矿区生态"],
        "keywords": ["绿色矿山", "生态修复", "土地复垦", "水土保持", "生物多样性"],
    },
    {
        "issue_id": "water_and_pollution",
        "issue_name": "水资源、废水、废气、危废管理",
        "description": "煤矿和煤电环节的水资源、废水、废气、固废与危废合规管理。",
        "esg_dimensions": ["E"],
        "materiality_level": "medium",
        "related_segments": ["煤炭生产", "发电", "煤化工相关业务"],
        "keywords": ["水资源", "废水", "废气", "危废", "污染物排放"],
    },
    {
        "issue_id": "supply_chain_esg",
        "issue_name": "外购煤与供应链 ESG 管理",
        "description": "外购煤供应商准入、运输承包商、采购合规与供应链 ESG 风险。",
        "esg_dimensions": ["S", "G"],
        "materiality_level": "medium",
        "related_segments": ["煤炭销售", "铁路港口航运", "采购"],
        "keywords": ["外购煤", "供应链 ESG", "供应商管理", "承包商", "采购合规"],
    },
    {
        "issue_id": "related_party_governance",
        "issue_name": "关联交易与公司治理透明度",
        "description": "集团内交易、金融服务协议、互供协议和治理透明度。",
        "esg_dimensions": ["G"],
        "materiality_level": "high",
        "related_segments": ["公司治理", "财务", "投资者关系"],
        "keywords": ["关联交易", "互供协议", "金融服务协议", "股东大会", "公司治理"],
    },
    {
        "issue_id": "esg_data_governance",
        "issue_name": "ESG数据治理与评级披露",
        "description": "ESG 指标口径、内部控制、评级问卷、可持续披露准则映射。",
        "esg_dimensions": ["G"],
        "materiality_level": "high",
        "related_segments": ["ESG披露", "数据治理", "投资者关系"],
        "keywords": ["ESG数据治理", "ESG评级", "可持续披露", "ISSB", "指标口径"],
    },
]


LAYER_OBJECT_TYPES = {
    "rule": "RuleChange",
    "industry": "IndustrySignal",
    "company": "CompanyEvent",
    "peer": "PeerAction",
}

LAYER_SOURCE_HINTS = {
    "rule": ["国家发改委", "国家能源局", "生态环境部", "应急管理部", "国家矿山安全监察局", "ISSB / IFRS"],
    "industry": ["行业协会", "新华社", "央视网", "权威财经媒体"],
    "company": ["公司官网", "交易所公告", "年报 / ESG报告 / 可持续发展报告"],
    "peer": ["对标企业年报", "对标企业 ESG报告", "对标企业官网新闻", "交易所公告"],
}


RECOMMENDATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "climate_transition": {
        "recommendation": "建立能源转型情景与碳成本月度监测机制，按煤炭、煤电、运输板块跟踪碳价、政策约束、低碳投资和转型收入占比。",
        "owners": ["战略管理", "ESG披露", "财务"],
        "kpis": ["碳排放强度", "低碳投资金额", "转型收入占比", "碳价敏感性测算覆盖率"],
        "horizon": "3-6个月",
    },
    "coal_power_decarbonization": {
        "recommendation": "建立煤电机组节能降碳改造台账，逐台跟踪供电煤耗、灵活性改造进度、供热替代量和减排量。",
        "owners": ["环境管理", "发电业务", "ESG披露"],
        "kpis": ["供电煤耗", "灵活性改造容量", "节能改造项目完成率", "估算减排量"],
        "horizon": "6-12个月",
    },
    "mine_safety": {
        "recommendation": "建立煤矿安全生产月度 ESG 监测看板，覆盖百万工时伤害率、重大事故数量、隐患整改闭环率、承包商安全培训覆盖率和智能化工作面数量。",
        "owners": ["安全生产", "矿山运营", "ESG披露"],
        "kpis": ["百万工时伤害率", "重大事故数量", "隐患整改闭环率", "承包商安全培训覆盖率", "智能化工作面数量"],
        "horizon": "1-3个月",
    },
    "green_mine_ecology": {
        "recommendation": "将绿色矿山和生态修复项目纳入月度披露底稿，按矿区记录土地复垦面积、生态修复投入、验收进度和社区沟通情况。",
        "owners": ["环境管理", "矿山运营", "公共关系"],
        "kpis": ["土地复垦面积", "生态修复投入", "绿色矿山达标率", "生态项目验收率"],
        "horizon": "3-6个月",
    },
    "water_and_pollution": {
        "recommendation": "完善水资源与污染物排放的异常预警台账，按生产单元跟踪取水强度、废水回用率、主要污染物排放和危废合规处置率。",
        "owners": ["环境管理", "生产运营", "合规"],
        "kpis": ["取水强度", "废水回用率", "主要污染物达标率", "危废合规处置率"],
        "horizon": "3-6个月",
    },
    "supply_chain_esg": {
        "recommendation": "建立外购煤与承包商 ESG 分级管理机制，在准入、合同、履约评价中纳入安全、环保、劳工和商业道德指标。",
        "owners": ["采购", "安全生产", "合规治理"],
        "kpis": ["供应商 ESG 筛查覆盖率", "高风险供应商整改率", "承包商事故率", "供应商培训覆盖率"],
        "horizon": "6-12个月",
    },
    "related_party_governance": {
        "recommendation": "建立关联交易月度透明度底稿，跟踪协议额度使用率、定价依据、董事会和股东大会审议节点及独立董事意见披露完整性。",
        "owners": ["董事会办公室", "财务", "投资者关系"],
        "kpis": ["关联交易额度使用率", "审议披露及时率", "独立董事意见覆盖率", "定价依据归档完整率"],
        "horizon": "1-3个月",
    },
    "esg_data_governance": {
        "recommendation": "建设 ESG 数据治理矩阵，将评级问卷、ISSB/交易所披露要求和内部指标口径映射到责任部门、数据源、复核频率和留痕材料。",
        "owners": ["ESG披露", "数据管理", "投资者关系"],
        "kpis": ["核心指标留痕率", "跨部门复核完成率", "评级问卷响应周期", "披露口径差异整改数"],
        "horizon": "3-6个月",
    },
}
