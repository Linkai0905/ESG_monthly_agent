from __future__ import annotations

import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit

from esg_monthly_agent.config import (
    DEFAULT_MATERIALITY_TOPICS,
    LAYER_OBJECT_TYPES,
    LAYER_SOURCE_HINTS,
    RECOMMENDATION_TEMPLATES,
    SOURCE_PRIORITY_REGISTRY,
    USE_LOCAL_SOURCES,
    USE_SEED_EVIDENCE,
)
from esg_monthly_agent.schemas import (
    CompanyEvent,
    CompanyExposure,
    CompanyProfile,
    CustomerSegment,
    ESGDimension,
    EvidenceItem,
    EvidenceNeed,
    IndustryEvent,
    IssueChain,
    Layer,
    MaterialityTopic,
    ParsedDocument,
    PeerAction,
    QualityCheckResult,
    RawDocument,
    Recommendation,
    ReportContract,
    ReportSection,
    RuleChange,
    SearchTask,
    SourcePriority,
    SourceRecord,
    dump_model,
    stable_id,
)
from esg_monthly_agent.tools.local_sources import LocalManualSourceTool, LocalSource


def company_name(state: dict[str, Any]) -> str:
    company = state.get("company") or {}
    if isinstance(company, dict):
        return company.get("name") or company.get("company") or "中国神华"
    return str(company)


def period_label(state: dict[str, Any]) -> str:
    period = state.get("period") or {}
    return period.get("label") or (period.get("start") or "")[:7] or "unknown"


def period_year_month(state: dict[str, Any]) -> tuple[str, str]:
    label = period_label(state)
    if re.match(r"^\d{4}-\d{2}$", label):
        year, month = label.split("-")
        return year, str(int(month))
    return "2026", "6"


def _topic_models() -> list[MaterialityTopic]:
    return [MaterialityTopic.model_validate(topic) for topic in DEFAULT_MATERIALITY_TOPICS]


def _topic_by_id(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    topics = state.get("materiality_topics") or dump_model(_topic_models())
    return {topic["issue_id"]: topic for topic in topics}


def build_report_contract(state: dict[str, Any]) -> ReportContract:
    return ReportContract(
        company=company_name(state),
        period=state.get("period", {}),
        language=state.get("language", "zh-CN"),
        report_type=state.get("report_type", "monthly"),
        required_layers=["rule", "industry", "company", "peer"],
        required_outputs=[
            "markdown report",
            "evidence_items.json",
            "issue_chains.json",
            "recommendations.json",
            "quality_checks.json",
        ],
        reasoning_chain=[
            "规则变化",
            "行业传导",
            f"{company_name(state)}暴露",
            "对标企业关键行动",
            f"针对{company_name(state)}的建议",
        ],
        quality_rules=[
            "所有事实判断必须绑定 evidence_ids。",
            "缺证据时写入 missing_links 或 missing_evidence。",
            "建议必须包含行动、理由、ESG价值、责任部门、KPI、时间窗口。",
            "质量审查必须在报告生成之前执行。",
        ],
    )


def discover_company_boundary(state: dict[str, Any]) -> CompanyProfile:
    name = company_name(state)
    peers = state.get("peers") or ["中煤能源", "陕西煤业", "兖矿能源", "华能国际", "华电国际"]
    tickers = state.get("ticker") or ["601088.SH", "01088.HK"]

    if "神华" in name:
        return CompanyProfile(
            company=name,
            aliases=["中国神华", "中国神华能源", "China Shenhua", "中国神华能源股份有限公司"],
            tickers=tickers,
            industry=["煤炭开采", "煤电", "铁路运输", "港口航运", "煤化工相关"],
            business_segments=["煤炭生产", "煤炭销售", "发电", "铁路", "港口", "航运"],
            peers=peers,
            boundary_notes=[
                "报告对象边界覆盖上市公司及其披露口径内的煤炭、电力和运输相关业务。",
                "正式运行时应使用公司年报、ESG报告和交易所公告核验业务边界。",
            ],
            missing_evidence=["公司边界需用最近一期年报/ESG报告核验。"],
        )

    return CompanyProfile(
        company=name,
        aliases=[name],
        tickers=tickers,
        industry=state.get("industry") or [],
        business_segments=[],
        peers=peers,
        missing_evidence=["需要公司年报、官网和交易所公告确认业务边界。"],
    )


def map_customer_segments(state: dict[str, Any]) -> list[CustomerSegment]:
    profile = state.get("company_profile") or {}
    segments = profile.get("business_segments") or ["煤炭生产", "发电", "运输", "公司治理"]
    segment_specs = {
        "煤炭生产": ("coal_mining", "煤矿安全、生态修复、甲烷与水资源管理"),
        "煤炭销售": ("coal_sales", "外购煤、供应链 ESG、销售结构和运输排放"),
        "发电": ("power_generation", "煤电节能降碳、污染物排放、机组灵活性改造"),
        "铁路": ("railway", "运输能效、安全生产和供应链协同"),
        "港口": ("port", "港口污染防治、粉尘治理和安全运营"),
        "航运": ("shipping", "船舶能效、燃料排放和安全运营"),
    }
    output: list[CustomerSegment] = []
    for segment in segments:
        segment_id, touchpoint = segment_specs.get(
            segment, (stable_id("segment", segment), "需补充 ESG 触点")
        )
        output.append(
            CustomerSegment(
                segment_id=segment_id,
                segment_name=segment,
                description=f"{company_name(state)}的{segment}业务板块。",
                revenue_driver="主营业务贡献" if segment in {"煤炭生产", "煤炭销售", "发电"} else "运营协同",
                geography=["中国"],
                esg_touchpoints=[touchpoint],
                missing_evidence=["需用公司最新披露文件核验板块口径。"],
            )
        )
    return output


def build_materiality_topics(state: dict[str, Any]) -> list[MaterialityTopic]:
    return _topic_models()


def build_evidence_needs(state: dict[str, Any]) -> list[EvidenceNeed]:
    needs: list[EvidenceNeed] = []
    for topic in state.get("materiality_topics") or dump_model(_topic_models()):
        for layer, object_type in LAYER_OBJECT_TYPES.items():
            needs.append(
                EvidenceNeed(
                    need_id=f"need_{topic['issue_id']}_{layer}",
                    issue_id=topic["issue_id"],
                    layer=layer,
                    object_type=object_type,
                    description=(
                        f"为议题“{topic['issue_name']}”补齐 {layer} 层证据，"
                        "用于构建 RuleChange -> IndustrySignal -> CompanyEvent -> PeerAction 链条。"
                    ),
                    preferred_sources=LAYER_SOURCE_HINTS[layer],
                    min_items=1,
                )
            )
    return needs


def build_source_registry(state: dict[str, Any]) -> list[dict[str, Any]]:
    return SOURCE_PRIORITY_REGISTRY


def _special_queries(issue_id: str, layer: str, company: str, peers: list[str], year: str, month: str) -> list[str] | None:
    if issue_id == "mine_safety" and layer == "industry":
        return [
            f"煤矿安全监管 {year} {month}月",
            f"智能矿山 政策 煤矿 {year}",
            f"煤矿事故 监管通报 {year} {month}月",
        ]
    if issue_id == "related_party_governance" and layer == "company":
        return [
            f"{company} {year} {month} 财务公司 增资 公告",
            f"{company} 股东大会 互供协议 2027 2029",
            f"601088 关联交易 金融服务协议 {year}",
        ]
    return None


def _queries_for_task(topic: dict[str, Any], layer: str, state: dict[str, Any]) -> list[str]:
    company = company_name(state)
    peers = state.get("peers") or ["中煤能源", "陕西煤业", "兖矿能源"]
    year, month = period_year_month(state)
    special = _special_queries(topic["issue_id"], layer, company, peers, year, month)
    if special:
        return special

    keywords = topic.get("keywords") or [topic["issue_name"]]
    base = keywords[:3]
    if layer == "rule":
        return [f"{kw} 政策 标准 评级 {year} {month}月" for kw in base]
    if layer == "industry":
        return [f"{kw} 煤炭 行业 动态 最佳实践 {year} {month}月" for kw in base]
    if layer == "company":
        return [f"{company} {kw} 公告 ESG {year} {month}月" for kw in base]
    return [f"{peer} {base[0]} ESG 行动 {year} {month}月" for peer in peers[:3]]


def plan_search_tasks(state: dict[str, Any]) -> list[SearchTask]:
    period = state.get("period") or {}
    tasks: list[SearchTask] = []
    for topic in state.get("materiality_topics") or dump_model(_topic_models()):
        for layer, object_type in LAYER_OBJECT_TYPES.items():
            task_id = f"task_{topic['issue_id']}_{layer}"
            tasks.append(
                SearchTask(
                    task_id=task_id,
                    issue_id=topic["issue_id"],
                    layer=layer,
                    object_type=object_type,
                    search_goal=(
                        f"围绕重大议题“{topic['issue_name']}”检索 {layer} 层证据，"
                        "不得以泛 ESG 新闻作为主任务。"
                    ),
                    queries=_queries_for_task(topic, layer, state),
                    source_priority=["P0", "P1"] if layer in {"rule", "company", "peer"} else ["P0", "P1", "P2"],
                    target_sources=LAYER_SOURCE_HINTS[layer],
                    date_range={"start": period.get("start", ""), "end": period.get("end", "")},
                    min_results=1,
                    min_evidence_items=1,
                    required=True,
                    inclusion_criteria=[
                        f"必须能映射到 issue_id={topic['issue_id']}",
                        "必须能支持证据链中的一个明确环节",
                    ],
                    exclusion_criteria=["泛泛 ESG 新闻汇总", "无来源转载", "无法确认日期或发布主体的内容"],
                    expected_output_schema=object_type,
                    repair_strategy=f"若缺少 {layer} 层证据，优先扩大 P0/P1 来源和同义关键词。",
                )
            )
    return tasks


def generate_issue_queries(state: dict[str, Any]) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for task in state.get("search_tasks", []):
        for query in task.get("queries", []):
            generated.append(
                {
                    "task_id": task["task_id"],
                    "issue_id": task["issue_id"],
                    "layer": task["layer"],
                    "query": query,
                    "target_sources": task.get("target_sources", []),
                }
            )
    return generated


def _source_priority_for_layer(layer: str) -> SourcePriority:
    return SourcePriority.P1 if layer == "industry" else SourcePriority.P0


def _source_priority_from_manual(priority: int, layer: str) -> SourcePriority:
    if priority >= 4:
        return SourcePriority.P0
    if priority == 3:
        return SourcePriority.P1
    if priority == 2:
        return SourcePriority.P2
    return SourcePriority.P3


def _authority_from_priority(priority: SourcePriority) -> float:
    return {
        SourcePriority.P0: 0.95,
        SourcePriority.P1: 0.8,
        SourcePriority.P2: 0.55,
        SourcePriority.P3: 0.2,
    }[priority]


def _layer_matches_section(layer: str, section: str) -> bool:
    return {
        "rule": "policy",
        "industry": "industry",
        "company": "company",
        "peer": "peer",
    }.get(layer) == section


def _source_matches_topic(source: LocalSource, topic: dict[str, Any]) -> bool:
    haystack = " ".join([source.title, source.text, " ".join(source.tags)]).lower()
    probes = [topic.get("issue_name", ""), *topic.get("keywords", [])]
    return any(probe and probe.lower() in haystack for probe in probes)


def _best_local_sources_for_task(
    task: dict[str, Any],
    topic: dict[str, Any],
    local_sources: list[LocalSource],
) -> list[tuple[LocalSource, bool]]:
    layer_sources = [
        source for source in local_sources if _layer_matches_section(task["layer"], source.section_hint)
    ]
    exact = [source for source in layer_sources if _source_matches_topic(source, topic)]
    if exact:
        return [(source, False) for source in sorted(exact, key=lambda item: item.priority, reverse=True)[:2]]
    if not layer_sources:
        return []
    fallback = sorted(layer_sources, key=lambda item: item.priority, reverse=True)[:1]
    return [(source, True) for source in fallback]


def _seed_url(layer: str, issue_id: str) -> str:
    domains = {
        "rule": "https://www.ndrc.gov.cn/",
        "industry": "https://www.xinhuanet.com/",
        "company": "https://www.sse.com.cn/",
        "peer": "https://www.cninfo.com.cn/",
    }
    return f"{domains.get(layer, 'https://example.com/') }esg-monthly-agent-seed/{issue_id}/{layer}"


def _seed_text(task: dict[str, Any], topic: dict[str, Any], state: dict[str, Any]) -> str:
    company = company_name(state)
    layer = task["layer"]
    issue_name = topic["issue_name"]
    if layer == "rule":
        return (
            f"证据计划种子：围绕“{issue_name}”，正式检索应优先核验监管机构、交易所或评级机构在"
                        f"{period_label(state)}发布的规则、标准、评级方法或监管口径变化，并提取对{company}重大议题的约束。"
        )
    if layer == "industry":
        return (
            f"证据计划种子：围绕“{issue_name}”，正式检索应核验煤炭、电力或能源行业在"
            f"{period_label(state)}的风险动态、最佳实践和行业传导信号。"
        )
    if layer == "company":
        return (
            f"证据计划种子：围绕“{issue_name}”，正式检索应优先核验{company}官网、交易所公告、"
            "年报或 ESG 报告中的公司事件，并判断业务板块暴露。"
        )
    peers = state.get("peers") or ["中煤能源", "陕西煤业", "兖矿能源"]
    return (
        f"证据计划种子：围绕“{issue_name}”，正式检索应核验对标企业（如{peers[0]}）官网、年报、"
        "ESG 报告或交易所公告中的管理行动，并提取可对标做法。"
    )


def execute_search_tasks(state: dict[str, Any]) -> dict[str, Any]:
    local_sources = LocalManualSourceTool().load() if USE_LOCAL_SOURCES else []
    tasks = state.get("repair_search_tasks") or state.get("search_tasks", [])
    local_result = _execute_local_source_tasks(state, tasks, local_sources)
    if local_result["raw_documents"]:
        return local_result

    if not USE_SEED_EVIDENCE:
        return {
            "source_records": [],
            "raw_documents": [],
            "warnings": [
                {
                    "stage": "execute_issue_aware_search",
                    "message": "ESG_USE_SEED_EVIDENCE=false but real search tools are not configured.",
                }
            ],
        }

    existing_sources = {item.get("source_id") for item in state.get("source_records", [])}
    topics = _topic_by_id(state)
    sources: list[SourceRecord] = []
    docs: list[RawDocument] = []
    for task in tasks:
        issue_id = task["issue_id"]
        layer = task["layer"]
        topic = topics.get(issue_id, {"issue_name": issue_id, "esg_dimensions": ["Mixed"]})
        source_id = stable_id("source", task["task_id"], layer, "seed")
        if source_id in existing_sources:
            continue
        priority = _source_priority_for_layer(layer)
        authority = 1.0 if priority == SourcePriority.P0 else 0.8
        title = f"{topic['issue_name']} {layer} 层证据计划种子"
        publisher = (task.get("target_sources") or ["系统内置种子"])[0]
        sources.append(
            SourceRecord(
                source_id=source_id,
                task_id=task["task_id"],
                issue_id=issue_id,
                layer=layer,
                url=_seed_url(layer, issue_id),
                title=title,
                publisher=publisher,
                publish_date=(state.get("period") or {}).get("end"),
                priority=priority,
                source_type=task["object_type"],
                discovered_via="seed_evidence_for_smoke_test",
                authority_score=authority,
                freshness_score=0.65,
                relevance_score=0.8,
            )
        )
        docs.append(
            RawDocument(
                document_id=stable_id("raw", source_id),
                source_id=source_id,
                task_id=task["task_id"],
                issue_id=issue_id,
                layer=layer,
                source_url=_seed_url(layer, issue_id),
                source_title=title,
                publisher=publisher,
                publish_date=(state.get("period") or {}).get("end"),
                raw_text=_seed_text(task, topic, state),
                metadata={
                    "object_type": task["object_type"],
                    "source_priority": priority.value,
                    "authority_score": authority,
                    "freshness_score": 0.65,
                    "relevance_score": 0.8,
                    "issue_name": topic["issue_name"],
                    "esg_dimensions": topic.get("esg_dimensions") or ["Mixed"],
                    "seed": True,
                },
            )
        )
    return {
        "source_records": dump_model(sources),
        "raw_documents": dump_model(docs),
        "warnings": [
            {
                "stage": "execute_issue_aware_search",
                "message": "当前使用确定性种子证据跑通流程；生产环境需接入真实搜索、抓取与解析工具。",
            }
        ]
        if docs
        else [],
    }


def _execute_local_source_tasks(
    state: dict[str, Any],
    tasks: list[dict[str, Any]],
    local_sources: list[LocalSource],
) -> dict[str, Any]:
    if not local_sources or not tasks:
        return {"source_records": [], "raw_documents": [], "warnings": []}

    existing_sources = {item.get("source_id") for item in state.get("source_records", [])}
    topics = _topic_by_id(state)
    sources: list[SourceRecord] = []
    docs: list[RawDocument] = []
    warnings: list[dict[str, Any]] = []
    unmatched_tasks = 0

    for task in tasks:
        issue_id = task["issue_id"]
        layer = task["layer"]
        topic = topics.get(issue_id, {"issue_name": issue_id, "esg_dimensions": ["Mixed"]})
        matches = _best_local_sources_for_task(task, topic, local_sources)
        if not matches:
            unmatched_tasks += 1
            continue
        for source, fallback_match in matches:
            source_identity = source.public_url or str(source.path or source.title)
            source_id = stable_id("source", task["task_id"], source_identity)
            if source_id in existing_sources:
                continue
            priority = _source_priority_from_manual(source.priority, layer)
            authority = _authority_from_priority(priority)
            relevance = 0.86 if not fallback_match else 0.58
            source_url = source.public_url
            source_local_path = str(source.path) if source.path else ""
            source_note = source.note or (
                "本地文件已解析，但没有可验证公网 URL。" if source_local_path and not source_url else ""
            )
            sources.append(
                SourceRecord(
                    source_id=source_id,
                    task_id=task["task_id"],
                    issue_id=issue_id,
                    layer=layer,
                    url=source_url,
                    local_path=source_local_path,
                    is_sample_source=source.is_sample_source or not bool(source_url),
                    source_note=source_note,
                    title=source.title,
                    publisher=source.publisher,
                    publish_date=source.expected_date or (state.get("period") or {}).get("end"),
                    priority=priority,
                    source_type=task["object_type"],
                    discovered_via="local_manual_sources",
                    authority_score=authority,
                    freshness_score=0.72,
                    relevance_score=relevance,
                )
            )
            docs.append(
                RawDocument(
                    document_id=stable_id("raw", source_id),
                    source_id=source_id,
                    task_id=task["task_id"],
                    issue_id=issue_id,
                    layer=layer,
                    source_url=source_url,
                    source_local_path=source_local_path,
                    is_sample_source=source.is_sample_source or not bool(source_url),
                    source_note=source_note,
                    source_title=source.title,
                    publisher=source.publisher,
                    publish_date=source.expected_date or (state.get("period") or {}).get("end"),
                    raw_text=source.text,
                    metadata={
                        "object_type": task["object_type"],
                        "source_priority": priority.value,
                        "authority_score": authority,
                        "freshness_score": 0.72,
                        "relevance_score": relevance,
                        "issue_name": topic["issue_name"],
                        "esg_dimensions": topic.get("esg_dimensions") or ["Mixed"],
                        "local_source": True,
                        "source_local_path": source_local_path,
                        "is_sample_source": source.is_sample_source or not bool(source_url),
                        "source_note": source_note,
                        "fallback_match": fallback_match,
                        "missing_evidence": [
                            "该本地材料为同层补强证据，需用更精确来源补证。"
                        ]
                        if fallback_match
                        else [],
                    },
                )
            )

    if local_sources:
        warnings.append(
            {
                "stage": "execute_issue_aware_search",
                "message": (
                    f"Loaded {len(docs)} local manual-source documents for issue-aware tasks; "
                    f"{unmatched_tasks} tasks had no same-layer local source."
                ),
            }
        )
    return {
        "source_records": dump_model(sources),
        "raw_documents": dump_model(docs),
        "warnings": warnings,
    }


def parse_raw_documents(state: dict[str, Any]) -> list[ParsedDocument]:
    existing = {doc.get("document_id") for doc in state.get("parsed_documents", [])}
    parsed: list[ParsedDocument] = []
    for raw in state.get("raw_documents", []):
        if raw["document_id"] in existing:
            continue
        parsed.append(
            ParsedDocument(
                document_id=raw["document_id"],
                source_id=raw["source_id"],
                task_id=raw["task_id"],
                issue_id=raw["issue_id"],
                layer=raw["layer"],
                source_url=raw["source_url"],
                source_local_path=raw.get("source_local_path", ""),
                is_sample_source=raw.get("is_sample_source", False),
                source_note=raw.get("source_note", ""),
                source_title=raw["source_title"],
                publisher=raw["publisher"],
                publish_date=raw.get("publish_date"),
                text=raw.get("raw_text", "").strip(),
                metadata=raw.get("metadata", {}),
            )
        )
    return parsed


def extract_evidence_items(state: dict[str, Any]) -> list[EvidenceItem]:
    existing = {item.get("evidence_id") for item in state.get("evidence_items", [])}
    items: list[EvidenceItem] = []
    for doc in state.get("parsed_documents", []):
        evidence_id = stable_id("ev", doc["document_id"], doc["issue_id"], doc["layer"])
        if evidence_id in existing:
            continue
        metadata = doc.get("metadata") or {}
        dims = metadata.get("esg_dimensions") or ["Mixed"]
        dim = dims[0] if dims else "Mixed"
        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                source_url=doc["source_url"],
                source_local_path=doc.get("source_local_path", ""),
                is_sample_source=doc.get("is_sample_source", False)
                or bool((doc.get("metadata") or {}).get("is_sample_source")),
                source_note=doc.get("source_note", "")
                or (doc.get("metadata") or {}).get("source_note", ""),
                source_title=doc["source_title"],
                publisher=doc["publisher"],
                publish_date=doc.get("publish_date"),
                text=doc.get("text", ""),
                related_company=company_name(state),
                related_issues=[doc["issue_id"]],
                layer=doc["layer"],
                object_type=metadata.get("object_type") or LAYER_OBJECT_TYPES.get(doc["layer"], "Evidence"),
                esg_dimension=dim,
                authority_score=metadata.get("authority_score", 0.6),
                freshness_score=metadata.get("freshness_score", 0.6),
                relevance_score=metadata.get("relevance_score", 0.7),
                source_priority=metadata.get("source_priority", "P1"),
                evidence_type=metadata.get("object_type") or LAYER_OBJECT_TYPES.get(doc["layer"], "Evidence"),
                quote=(doc.get("text", "")[:180]),
                missing_evidence=metadata.get("missing_evidence", [])
                or (["正式报告需用真实来源替换种子证据。"] if metadata.get("seed") else []),
            )
        )
    return items


def classify_events(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    existing_rule = {item.get("rule_id") for item in state.get("rule_changes", [])}
    existing_industry = {item.get("event_id") for item in state.get("industry_events", [])}
    existing_company = {item.get("event_id") for item in state.get("company_events", [])}
    existing_peer = {item.get("peer_action_id") for item in state.get("peer_actions", [])}
    topics = _topic_by_id(state)

    rules: list[RuleChange] = []
    industry_events: list[IndustryEvent] = []
    company_events: list[CompanyEvent] = []
    peer_actions: list[PeerAction] = []

    for event_key, evidence_group in _group_evidence_for_events(state.get("evidence_items", [])).items():
        evidence = _representative_evidence(evidence_group)
        issue_id = event_key[0]
        topic = topics.get(issue_id, {"issue_name": issue_id, "related_segments": ["待确认"]})
        layer = event_key[1]
        evidence_ids = _unique_ordered(item["evidence_id"] for item in evidence_group)
        missing_evidence = _merged_missing_evidence(evidence_group)
        if layer == "rule":
            rule_id = stable_id("rule", *event_key)
            if rule_id not in existing_rule:
                rules.append(
                    RuleChange(
                        rule_id=rule_id,
                        issue_id=issue_id,
                        title=f"{topic['issue_name']}相关规则动态",
                        rule_type=evidence["object_type"],
                        publisher=evidence["publisher"],
                        publish_date=evidence.get("publish_date"),
                        summary=_summarize_text(evidence["text"]),
                        expected_impact=f"需要映射到{company_name(state)}的{topic['issue_name']}管理要求。",
                        evidence_ids=evidence_ids,
                        source_priority=evidence["source_priority"],
                        missing_evidence=missing_evidence,
                    )
                )
        elif layer == "industry":
            event_id = stable_id("industry", *event_key)
            if event_id not in existing_industry:
                industry_events.append(
                    IndustryEvent(
                        event_id=event_id,
                        issue_id=issue_id,
                        title=f"{topic['issue_name']}行业信号",
                        event_type=evidence["object_type"],
                        summary=_summarize_text(evidence["text"]),
                        industry_signal=f"行业层面对{topic['issue_name']}的管理要求或最佳实践正在形成。",
                        esg_dimension=evidence["esg_dimension"],
                        evidence_ids=evidence_ids,
                        missing_evidence=missing_evidence,
                    )
                )
        elif layer == "company":
            event_id = stable_id("company", *event_key)
            if event_id not in existing_company:
                company_events.append(
                    CompanyEvent(
                        event_id=event_id,
                        issue_id=issue_id,
                        company=company_name(state),
                        business_segment=(topic.get("related_segments") or ["待确认"])[0],
                        title=f"{company_name(state)}：{topic['issue_name']}相关公司动态",
                        summary=_summarize_text(evidence["text"]),
                        esg_impact_hint=f"该动态需要评估对{topic['issue_name']}的 E/S/G 影响。",
                        esg_dimension=evidence["esg_dimension"],
                        evidence_ids=evidence_ids,
                        missing_evidence=missing_evidence,
                    )
                )
        elif layer == "peer":
            action_id = stable_id("peer", *event_key)
            if action_id not in existing_peer:
                peers = state.get("peers") or ["对标企业"]
                peer_actions.append(
                    PeerAction(
                        peer_action_id=action_id,
                        issue_id=issue_id,
                        peer_company=peers[0],
                        action=f"{topic['issue_name']}相关对标企业 ESG 关键行动",
                        action_type=evidence["object_type"],
                        benchmark_value=f"作为{company_name(state)}管理行动设计的对标线索，正式报告需核验证据。",
                        esg_dimension=evidence["esg_dimension"],
                        evidence_ids=evidence_ids,
                        missing_evidence=missing_evidence,
                        confidence=0.72,
                    )
                )

    return {
        "rule_changes": dump_model(rules),
        "industry_events": dump_model(industry_events),
        "company_events": dump_model(company_events),
        "peer_actions": dump_model(peer_actions),
    }


def build_issue_chains(state: dict[str, Any]) -> list[IssueChain]:
    topics = _topic_by_id(state)
    rules = _group_by_issue(state.get("rule_changes", []), "issue_id")
    industry = _group_by_issue(state.get("industry_events", []), "issue_id")
    company_events = _group_by_issue(state.get("company_events", []), "issue_id")
    peers = _group_by_issue(state.get("peer_actions", []), "issue_id")
    chains: list[IssueChain] = []

    for issue_id, topic in topics.items():
        rule_ids = [item["rule_id"] for item in rules.get(issue_id, [])]
        industry_ids = [item["event_id"] for item in industry.get(issue_id, [])]
        company_ids = [item["event_id"] for item in company_events.get(issue_id, [])]
        peer_ids = [item["peer_action_id"] for item in peers.get(issue_id, [])]
        missing = []
        if not rule_ids:
            missing.append("rule")
        if not industry_ids:
            missing.append("industry")
        if not company_ids:
            missing.append("company")
        if not peer_ids:
            missing.append("peer")
        present_count = 4 - len(missing)
        issue_name = topic["issue_name"]
        logic_parts = [
            "规则变化趋严或披露口径变化" if rule_ids else "规则变化待补证",
            "行业管理压力和最佳实践传导" if industry_ids else "行业传导待补证",
            f"{company_name(state)}相关业务板块暴露" if company_ids else f"{company_name(state)}暴露待补证",
            "对标企业已形成可对标行动" if peer_ids else "对标企业行动待补证",
            f"形成针对{company_name(state)}的建议",
        ]
        chains.append(
            IssueChain(
                issue_id=issue_id,
                issue_name=issue_name,
                rule_change_ids=rule_ids,
                industry_event_ids=industry_ids,
                company_event_ids=company_ids,
                peer_action_ids=peer_ids,
                chain_summary=f"{issue_name}链条覆盖 {present_count}/4 类证据。",
                logic_path=" → ".join(logic_parts),
                missing_links=missing,
                confidence=min(0.95, 0.35 + present_count * 0.15),
            )
        )
    return chains


def assess_company_exposure(state: dict[str, Any]) -> list[CompanyExposure]:
    topics = _topic_by_id(state)
    evidence_by_event = _evidence_ids_by_event(state)
    exposures: list[CompanyExposure] = []
    for chain in state.get("issue_chains", []):
        topic = topics.get(chain["issue_id"], {})
        dims = topic.get("esg_dimensions") or ["Mixed"]
        evidence_ids = _chain_evidence_ids(chain, evidence_by_event)
        risk = "high" if topic.get("materiality_level") == "high" else "medium"
        opportunity = "medium" if chain.get("peer_action_ids") else "low"
        exposures.append(
            CompanyExposure(
                exposure_id=stable_id("exposure", chain["issue_id"], company_name(state)),
                issue_id=chain["issue_id"],
                company=company_name(state),
                affected_segments=topic.get("related_segments") or ["待确认业务板块"],
                esg_dimension=dims[0],
                risk_level=risk,
                opportunity_level=opportunity,
                rationale=(
                    f"{chain['logic_path']}。因此需要判断{company_name(state)}在"
                    f"{'、'.join(topic.get('related_segments') or ['相关业务'])}的管理暴露。"
                ),
                evidence_ids=evidence_ids,
                missing_evidence=chain.get("missing_links", []),
                confidence=chain.get("confidence", 0.5),
            )
        )
    return exposures


def benchmark_peers(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("peer_actions"):
        return {"warnings": []}
    return {
        "warnings": [
            {
                "stage": "peer_benchmark",
                "message": "未提取到对标企业行动，建议扩大对标企业年报、ESG报告和官网新闻检索。",
            }
        ]
    }


def synthesize_recommendations(state: dict[str, Any]) -> list[Recommendation]:
    evidence_by_event = _evidence_ids_by_event(state)
    recs: list[Recommendation] = []
    chains = {chain["issue_id"]: chain for chain in state.get("issue_chains", [])}
    for exposure in state.get("company_exposures", []):
        issue_id = exposure["issue_id"]
        chain = chains.get(issue_id)
        if not chain:
            continue
        template = RECOMMENDATION_TEMPLATES.get(issue_id, {})
        evidence_ids = _chain_evidence_ids(chain, evidence_by_event)
        if not evidence_ids:
            continue
        priority = "high" if exposure.get("risk_level") == "high" else "medium"
        recs.append(
            Recommendation(
                recommendation_id=stable_id("rec", company_name(state), issue_id),
                issue_id=issue_id,
                company=company_name(state),
                recommendation=template.get(
                    "recommendation",
                    f"围绕{issue_id}建立月度 ESG 管理闭环，明确行动、责任、KPI和复核机制。",
                ),
                rationale=(
                    f"该建议来自证据链：{chain['logic_path']}；{company_name(state)}暴露判断："
                    f"{exposure['rationale']}"
                ),
                expected_esg_value="提升风险预警、披露可审计性和与对标企业比较的管理成熟度。",
                action_owner=template.get("owners", ["ESG披露", "相关业务部门"]),
                suggested_kpis=template.get("kpis", ["证据覆盖率", "整改闭环率", "披露及时率"]),
                time_horizon=template.get("horizon", "3-6个月"),
                evidence_ids=evidence_ids,
                related_rule_ids=chain.get("rule_change_ids", []),
                related_industry_event_ids=chain.get("industry_event_ids", []),
                related_company_event_ids=chain.get("company_event_ids", []),
                related_peer_action_ids=chain.get("peer_action_ids", []),
                priority=priority,
                confidence=min(0.92, chain.get("confidence", 0.5) + 0.05),
            )
        )
    return recs


def review_quality(state: dict[str, Any]) -> QualityCheckResult:
    missing_links: list[str] = []
    weak_recommendations: list[str] = []
    unsupported_claims: list[str] = []
    low_authority_sources: list[str] = []
    sample_sources: list[str] = []
    coverage_gaps: list[str] = []
    stale_sources: list[str] = []
    notes: list[str] = []
    period = state.get("period") or {}
    period_start = period.get("start")
    period_end = period.get("end")

    for chain in state.get("issue_chains", []):
        for link in chain.get("missing_links", []):
            missing_links.append(f"{chain['issue_id']}:{link}")

    evidence = {item["evidence_id"]: item for item in state.get("evidence_items", [])}
    for rec in state.get("recommendations", []):
        if not rec.get("evidence_ids"):
            weak_recommendations.append(f"{rec['recommendation_id']}: missing evidence_ids")
        if not rec.get("action_owner") or not rec.get("suggested_kpis") or not rec.get("time_horizon"):
            weak_recommendations.append(f"{rec['recommendation_id']}: missing owner/kpi/time_horizon")
        if rec.get("priority") == "high":
            categories = sum(
                bool(rec.get(field))
                for field in ["related_rule_ids", "related_company_event_ids", "related_peer_action_ids"]
            )
            if categories < 2:
                weak_recommendations.append(
                    f"{rec['recommendation_id']}: high priority needs two of rule/company/peer evidence"
                )
        for evidence_id in rec.get("evidence_ids", []):
            item = evidence.get(evidence_id)
            if item and item.get("source_priority") in {"P2", "P3"} and rec.get("priority") == "high":
                low_authority_sources.append(f"{rec['recommendation_id']}:{evidence_id}")

    for evidence_id, item in evidence.items():
        if item.get("is_sample_source") or not str(item.get("source_url", "")).startswith(
            ("http://", "https://")
        ):
            sample_sources.append(evidence_id)
        publish_date = item.get("publish_date")
        if publish_date and period_start and publish_date < period_start:
            stale_sources.append(evidence_id)
        if publish_date and period_end and publish_date > period_end:
            stale_sources.append(evidence_id)

    high_topics = {
        topic["issue_id"]
        for topic in state.get("materiality_topics", [])
        if topic.get("materiality_level") == "high"
    }
    covered_topics = {rec["issue_id"] for rec in state.get("recommendations", [])}
    for issue_id in sorted(high_topics - covered_topics):
        coverage_gaps.append(issue_id)

    if not state.get("company_exposures"):
        unsupported_claims.append(f"缺少{company_name(state)}影响判断。")
    for exposure in state.get("company_exposures", []):
        if not exposure.get("affected_segments"):
            unsupported_claims.append(f"{exposure['exposure_id']}: missing affected_segments")

    if any((item.get("missing_evidence") for item in state.get("evidence_items", []))):
        notes.append("当前存在同层补强或待补证据，正式交付前需用更精确来源复核。")
    if sample_sources:
        notes.append("当前存在本地样本或缺少公网 URL 的证据，不能作为正式报告来源。")

    passed = not (
        missing_links
        or weak_recommendations
        or unsupported_claims
        or low_authority_sources
        or sample_sources
        or stale_sources
        or coverage_gaps
    )
    repairable = not passed and (state.get("repair_attempts", 0) < 1) and not sample_sources
    return QualityCheckResult(
        passed=passed,
        repairable=repairable,
        missing_links=missing_links,
        weak_recommendations=weak_recommendations,
        unsupported_claims=unsupported_claims,
        low_authority_sources=low_authority_sources,
        sample_sources=sorted(set(sample_sources)),
        stale_sources=sorted(set(stale_sources)),
        coverage_gaps=coverage_gaps,
        notes=notes,
    )


def build_repair_tasks(state: dict[str, Any]) -> list[SearchTask]:
    quality = state.get("quality_checks") or {}
    missing = quality.get("missing_links") or []
    tasks_by_id = {task["task_id"]: task for task in state.get("search_tasks", [])}
    repairs: list[SearchTask] = []
    for item in missing:
        if ":" not in item:
            continue
        issue_id, layer = item.split(":", 1)
        base_task = tasks_by_id.get(f"task_{issue_id}_{layer}")
        if not base_task:
            continue
        repair = dict(base_task)
        repair["task_id"] = f"repair_{state.get('repair_attempts', 0) + 1}_{issue_id}_{layer}"
        repair["queries"] = [f"{query} 补充证据 官方" for query in base_task.get("queries", [])]
        repair["repair_strategy"] = "质量审查触发的定向补搜：优先补齐缺失链条。"
        repairs.append(SearchTask.model_validate(repair))
    return repairs


def write_report(state: dict[str, Any]) -> dict[str, Any]:
    company = company_name(state)
    period = state.get("period") or {}
    evidence = {item["evidence_id"]: item for item in state.get("evidence_items", [])}
    lines: list[str] = [
        f"# ESG月报：{company}｜{period.get('start', '')} 至 {period.get('end', '')}",
        "",
        "## 0. 本月摘要",
        f"- 本报告按“规则变化 → 行业传导 → {company}暴露 → 对标企业关键行动 → 针对{company}的建议”组织。",
        f"- 本月形成 {len(state.get('issue_chains', []))} 条 IssueChain、{len(state.get('recommendations', []))} 条建议。",
        f"- 质量审查结果：{'通过' if (state.get('quality_checks') or {}).get('passed') else '需补证'}。",
        "",
        "## 1. ESG政策、评级、标准动态",
        "### 1.1 本月外部规则变化",
    ]
    for rule in _limit_events_for_report(state.get("rule_changes", [])):
        lines.append(f"- **{rule['title']}**：{rule['summary']}（证据：{', '.join(rule['evidence_ids'])}）")
    lines.extend(["", f"### 1.2 对{company} ESG 议题的映射"])
    for chain in state.get("issue_chains", []):
        lines.append(f"- {chain['issue_name']}：{chain['chain_summary']}；缺口：{', '.join(chain['missing_links']) or '无'}")
    lines.extend(["", "### 1.3 潜在影响等级"])
    for exposure in state.get("company_exposures", []):
        lines.append(
            f"- {exposure['issue_id']}：风险 {exposure['risk_level']}，机会 {exposure['opportunity_level']}，"
            f"板块：{'、'.join(exposure['affected_segments'])}"
        )

    lines.extend(["", f"## 2. {company}所属行业新闻与最佳实践", "### 2.1 行业风险动态"])
    for event in _limit_events_for_report(state.get("industry_events", [])):
        lines.append(f"- {event['title']}：{event['industry_signal']}（证据：{', '.join(event['evidence_ids'])}）")
    lines.extend(["", "### 2.2 行业机会动态", "- 见各 IssueChain 的行业传导和对标企业关键行动部分。"])
    lines.extend(["", "### 2.3 行业最佳实践", "- 优先使用行业协会、央企官网和权威媒体来源，低权威来源仅作线索。"])

    lines.extend(["", f"## 3. {company}公司动态、ESG影响与对标企业关键行动", f"### 3.1 {company}本月动态"])
    for event in _limit_events_for_report(state.get("company_events", [])):
        lines.append(
            f"- {event['title']}：{event['summary']}（业务板块：{event['business_segment']}；"
            f"证据：{', '.join(event['evidence_ids'])}）"
        )
    lines.extend(["", "### 3.2 ESG影响判断"])
    for exposure in state.get("company_exposures", []):
        lines.append(f"- {exposure['issue_id']}：{exposure['rationale']}（证据：{', '.join(exposure['evidence_ids'])}）")
    lines.extend(["", "### 3.3 对标企业关键行动"])
    for peer in _limit_events_for_report(state.get("peer_actions", [])):
        lines.append(
            f"- {peer['peer_company']}：{peer['action']}；对标价值：{peer['benchmark_value']}"
            f"（证据：{', '.join(peer['evidence_ids'])}）"
        )
    lines.extend(["", f"### 3.4 针对{company}的管理建议"])
    for rec in state.get("recommendations", []):
        lines.append(
            f"- **{rec['priority']}｜{rec['issue_id']}**：{rec['recommendation']} "
            f"责任部门：{'、'.join(rec['action_owner'])}；KPI：{'、'.join(rec['suggested_kpis'])}；"
            f"时间窗口：{rec['time_horizon']}。"
        )

    lines.extend(["", "## 4. 重点议题链分析"])
    for chain in state.get("issue_chains", []):
        lines.extend(
            [
                f"### {chain['issue_name']}",
                f"- 外部规则变化：{', '.join(chain['rule_change_ids']) or '缺证据'}",
                f"- 行业落地表现：{', '.join(chain['industry_event_ids']) or '缺证据'}",
                f"- {company}暴露：{', '.join(chain['company_event_ids']) or '缺证据'}",
                f"- 对标企业行动：{', '.join(chain['peer_action_ids']) or '缺证据'}",
                f"- 逻辑链：{chain['logic_path']}",
            ]
        )

    lines.extend(
        [
            "",
            "## 5. 下月跟踪清单",
            "- 政策跟踪：监管机构、交易所、评级机构官方文件。",
            "- 行业跟踪：行业协会、央企官网、权威媒体和最佳实践。",
            "- 公司公告跟踪：公司官网、上交所、港交所、年报和 ESG 报告。",
            "- 对标企业行动跟踪：对标企业年报、ESG报告、官网新闻和交易所公告。",
            "- 数据指标跟踪：建议 KPI 的责任部门、数据源、复核频率和留痕材料。",
            "",
            "## 6. 证据附录",
            "| evidence_id | source | date | URL | 来源状态 | 对应议题 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for evidence_id, item in evidence.items():
        lines.append(
            f"| {evidence_id} | {item['publisher']} - {item['source_title']} | "
        f"{item.get('publish_date') or ''} | {_appendix_url_cell(item)} | "
        f"{_appendix_source_status(item)} | {', '.join(item['related_issues'])} |"
    )

    sections = {
        "0_summary": ReportSection(
            section_id="0_summary",
            title="本月摘要",
            content_markdown="\n".join(lines[:6]),
            evidence_ids=[],
        )
    }
    return {
        "report_markdown": "\n".join(lines) + "\n",
        "report_sections": dump_model(sections),
    }


def _group_by_issue(items: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[item[field]].append(item)
    return grouped


def _group_evidence_for_events(evidence_items: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for evidence in evidence_items:
        if not evidence.get("related_issues"):
            continue
        key = _event_group_key(evidence)
        grouped[key].append(evidence)
    return grouped


def _event_group_key(evidence: dict[str, Any]) -> tuple[str, str, str, str]:
    issue_id = evidence["related_issues"][0]
    layer = evidence.get("layer", "")
    object_type = evidence.get("object_type", "")
    source_note = str(evidence.get("source_note") or "")
    if source_note.startswith("deepsearch_claim:"):
        marker = source_note
    else:
        marker = _normalized_summary(evidence.get("text", "")) or _canonical_source_key(evidence)
    return issue_id, layer, object_type, marker


def _normalized_summary(text: str, max_chars: int = 180) -> str:
    summary = _summarize_text(text, max_chars=max_chars)
    return re.sub(r"\W+", "", summary.casefold())[:120]


def _canonical_source_key(evidence: dict[str, Any]) -> str:
    url = evidence.get("source_url") or ""
    try:
        parsed = urlsplit(url)
    except ValueError:
        parsed = None
    if parsed and parsed.netloc:
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.netloc.casefold().removeprefix('www.')}:{path.casefold()}"
    return f"{evidence.get('publisher', '')}:{evidence.get('source_title', '')}".casefold()


def _representative_evidence(evidence_group: list[dict[str, Any]]) -> dict[str, Any]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

    def sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        priority = str(item.get("source_priority") or "P3")
        return (
            priority_rank.get(priority, 9),
            str(item.get("publish_date") or ""),
            len(str(item.get("text") or "")),
        )

    return sorted(evidence_group, key=sort_key)[0]


def _merged_missing_evidence(evidence_group: list[dict[str, Any]]) -> list[str]:
    return sorted({item for evidence in evidence_group for item in evidence.get("missing_evidence", [])})


def _unique_ordered(values: Any) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _limit_events_for_report(items: list[dict[str, Any]], max_per_issue: int = 3) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    output: list[dict[str, Any]] = []
    for item in items:
        issue_id = item.get("issue_id", "")
        if counts[issue_id] >= max_per_issue:
            continue
        counts[issue_id] += 1
        output.append(item)
    return output


def _evidence_ids_by_event(state: dict[str, Any]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for rule in state.get("rule_changes", []):
        mapping[rule["rule_id"]] = rule.get("evidence_ids", [])
    for event in state.get("industry_events", []):
        mapping[event["event_id"]] = event.get("evidence_ids", [])
    for event in state.get("company_events", []):
        mapping[event["event_id"]] = event.get("evidence_ids", [])
    for peer in state.get("peer_actions", []):
        mapping[peer["peer_action_id"]] = peer.get("evidence_ids", [])
    return mapping


def _chain_evidence_ids(chain: dict[str, Any], evidence_by_event: dict[str, list[str]]) -> list[str]:
    ids: list[str] = []
    for field in ["rule_change_ids", "industry_event_ids", "company_event_ids", "peer_action_ids"]:
        for event_id in chain.get(field, []):
            ids.extend(evidence_by_event.get(event_id, []))
    return sorted(set(ids))


def _summarize_text(text: str, max_chars: int = 260) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_chars:
        return cleaned
    sentence_endings = ["。", "；", ".", ";"]
    best_cut = -1
    for mark in sentence_endings:
        idx = cleaned.find(mark, 80)
        if idx != -1:
            best_cut = idx + 1
            break
    if best_cut == -1 or best_cut > max_chars:
        best_cut = max_chars
    return cleaned[:best_cut].rstrip() + "..."


def _appendix_url_cell(item: dict[str, Any]) -> str:
    url = item.get("source_url") or ""
    if url.startswith(("http://", "https://")):
        return url
    return "待替换真实来源"


def _appendix_source_status(item: dict[str, Any]) -> str:
    if item.get("is_sample_source"):
        return "本地样本/非正式来源"
    if item.get("source_local_path") and not item.get("source_url"):
        return "本地文件已解析/非正式链接"
    if item.get("source_local_path"):
        return "本地副本已解析"
    return "正式来源"
