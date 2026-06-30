from __future__ import annotations

from esg_monthly_agent.schemas.deepsearch import (
    DeepSearchCitation,
    DeepSearchClaim,
    DeepSearchResult,
    DeepSearchTask,
    ReflectionResult,
)
from esg_monthly_agent.skills.deepsearch.decide_research_next_step.runner import (
    decide_research_next_step,
)
from esg_monthly_agent.skills.deepsearch.reflect_deepsearch.runner import (
    reflect_deepsearch_result,
)


def _task() -> DeepSearchTask:
    return DeepSearchTask(
        task_id="deep_task",
        issue_id="mine_safety",
        layer="company",
        object_type="CompanyEvent",
        company="中国神华",
        period={"label": "2026-06"},
        research_goal="研究公司事件",
        initial_question="检索公司公告",
        required_evidence=["公司公告"],
        source_policy={},
        expected_output_schema="CompanyEvent",
    )


def _result() -> DeepSearchResult:
    return DeepSearchResult(
        task_id="deep_task",
        issue_id="mine_safety",
        provider="openai_web_search",
        status="partial",
        answer_summary="partial",
        confidence=0.3,
    )


def _reflection(enough: bool) -> ReflectionResult:
    return ReflectionResult(
        task_id="deep_task",
        issue_id="mine_safety",
        relevant=enough,
        enough=enough,
        source_quality_ok=enough,
        freshness_ok=enough,
        layer_coverage_ok=enough,
        citation_quality_ok=enough,
        missing_evidence=[] if enough else ["缺少官方来源"],
        suggested_followup_question="继续查官方公告" if not enough else None,
        confidence=0.8 if enough else 0.3,
    )


def _reflection_with_provider_switch() -> ReflectionResult:
    return ReflectionResult(
        task_id="deep_task",
        issue_id="mine_safety",
        relevant=True,
        enough=False,
        source_quality_ok=False,
        freshness_ok=True,
        layer_coverage_ok=True,
        citation_quality_ok=False,
        missing_evidence=["缺少官方来源"],
        suggested_followup_question="继续查官方公告",
        suggested_provider="tavily_official_search",
        confidence=0.3,
    )


def test_decide_need_more_when_not_enough_and_rounds_remain():
    decision = decide_research_next_step(_task(), _result(), _reflection(False), 1, 3)

    assert decision.action == "need_more"
    assert decision.next_task is not None


def test_decide_switches_to_official_provider_when_suggested():
    decision = decide_research_next_step(_task(), _result(), _reflection_with_provider_switch(), 1, 3)

    assert decision.action == "switch_provider"
    assert decision.next_task is not None
    assert decision.next_task.provider == "tavily_official_search"


def test_reflection_suggests_official_provider_for_weak_zhipu_result():
    task = _task().model_copy(update={"allowed_domains": ["shenhuachina.com", "sse.com.cn"]})
    result = _result().model_copy(update={"provider": "zhipu_web_search", "answer_summary": "P2 lead only"})

    reflection = reflect_deepsearch_result(task, result)

    assert reflection.suggested_provider == "tavily_official_search"
    assert not reflection.source_quality_ok


def test_reflection_does_not_accept_p2_citations_as_source_quality():
    task = _task().model_copy(
        update={
            "layer": "industry",
            "object_type": "IndustrySignal",
            "allowed_domains": ["gov.cn", "xinhuanet.com"],
        }
    )
    result = _result().model_copy(
        update={
            "provider": "openai_web_search",
            "answer_summary": "2026-06 industry lead",
            "claims": [
                DeepSearchClaim(
                    claim_id="claim_p2",
                    text="industry lead",
                    claim_type="industry",
                    citation_ids=["cite_1", "cite_2"],
                )
            ],
            "citations": [
                DeepSearchCitation(
                    citation_id="cite_1",
                    title="market note",
                    url="https://example.com/a",
                    publish_date="2026-06-10",
                    source_priority="P2",
                ),
                DeepSearchCitation(
                    citation_id="cite_2",
                    title="market note 2",
                    url="https://example.com/b",
                    publish_date="2026-06-11",
                    source_priority="P2",
                ),
            ],
        }
    )

    reflection = reflect_deepsearch_result(task, result)

    assert not reflection.source_quality_ok
    assert reflection.suggested_provider == "tavily_official_search"


def test_decide_give_up_when_max_rounds_reached():
    decision = decide_research_next_step(_task(), _result(), _reflection(False), 3, 3)

    assert decision.action == "give_up"
    assert decision.stop_condition == "max_rounds"


def test_decide_enough_when_reflection_enough():
    decision = decide_research_next_step(_task(), _result(), _reflection(True), 1, 3)

    assert decision.action == "enough"
    assert decision.stop_condition == "evidence_ready"
