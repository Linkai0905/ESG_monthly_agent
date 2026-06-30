from __future__ import annotations

from esg_monthly_agent.skills.research_execution.evidence_from_deepsearch.runner import (
    extract_evidence_from_deepsearch,
)


def _state():
    task = {
        "task_id": "deep_task",
        "issue_id": "mine_safety",
        "layer": "company",
        "object_type": "CompanyEvent",
        "company": "中国神华",
        "period": {"label": "2026-06"},
        "research_goal": "研究公司事件",
        "initial_question": "检索公司公告",
        "required_evidence": ["公司公告"],
        "source_policy": {},
        "expected_output_schema": "CompanyEvent",
    }
    return {
        "company": {"name": "中国神华"},
        "deepsearch_tasks": [task],
        "deepsearch_decisions": [{"task_id": "deep_task", "issue_id": "mine_safety", "action": "enough"}],
        "deepsearch_results": [
            {
                "task_id": "deep_task",
                "issue_id": "mine_safety",
                "provider": "openai_web_search",
                "status": "completed",
                "answer_summary": "中国神华发布安全生产公告。",
                "claims": [
                    {
                        "claim_id": "claim_good",
                        "text": "中国神华发布安全生产公告。",
                        "claim_type": "company",
                        "evidence_urls": ["https://www.shenhuachina.com/news"],
                        "citation_ids": ["cite_good"],
                        "confidence": 0.8,
                    },
                    {
                        "claim_id": "claim_no_cite",
                        "text": "没有引用的事实。",
                        "claim_type": "company",
                        "evidence_urls": [],
                        "citation_ids": [],
                        "confidence": 0.2,
                    },
                    {
                        "claim_id": "claim_infer",
                        "text": "模型推断。",
                        "claim_type": "inference",
                        "evidence_urls": ["https://www.shenhuachina.com/news"],
                        "citation_ids": ["cite_good"],
                        "confidence": 0.2,
                    },
                ],
                "citations": [
                    {
                        "citation_id": "cite_good",
                        "title": "安全生产公告",
                        "url": "https://www.shenhuachina.com/news",
                        "publisher": "中国神华",
                        "publish_date": "2026-06-10",
                        "snippet_or_quote": "安全生产公告片段",
                        "source_priority": "P0",
                    }
                ],
                "sources": [],
                "tool_trace": [],
                "source_coverage": {},
                "missing_evidence": [],
                "uncertainty": [],
                "confidence": 0.8,
            }
        ],
        "evidence_items": [],
    }


def test_cited_non_inference_claim_becomes_evidence():
    items = extract_evidence_from_deepsearch(_state())

    assert len(items) == 1
    assert items[0].source_url == "https://www.shenhuachina.com/news"
    assert items[0].source_priority == "P0"
    assert items[0].text == "安全生产公告片段"
    assert items[0].quote == "安全生产公告片段"
    assert items[0].source_note.startswith("deepsearch_claim:deep_task:claim_good")
    assert "没有引用" not in items[0].text
    assert "模型推断" not in items[0].text


def test_evidence_text_does_not_duplicate_aggregate_claim_text_for_each_citation():
    state = _state()
    result = state["deepsearch_results"][0]
    result["claims"][0]["text"] = "聚合回答：1. 来源A 2. 来源B 3. 来源C"
    result["claims"][0]["citation_ids"] = ["cite_a", "cite_b", "cite_c"]
    result["citations"] = [
        {
            "citation_id": "cite_a",
            "title": "来源A",
            "url": "https://www.shenhuachina.com/a",
            "publisher": "中国神华",
            "publish_date": "2026-06-10",
            "snippet_or_quote": "来源A片段",
            "source_priority": "P0",
        },
        {
            "citation_id": "cite_b",
            "title": "来源B",
            "url": "https://www.shenhuachina.com/b",
            "publisher": "中国神华",
            "publish_date": "2026-06-11",
            "snippet_or_quote": "来源B片段",
            "source_priority": "P0",
        },
        {
            "citation_id": "cite_c",
            "title": "来源C",
            "url": "https://www.shenhuachina.com/c",
            "publisher": "中国神华",
            "publish_date": "2026-06-12",
            "snippet_or_quote": "来源C片段",
            "source_priority": "P0",
        },
    ]

    items = extract_evidence_from_deepsearch(state)

    assert [item.text for item in items] == ["来源A片段", "来源B片段", "来源C片段"]
    assert all(item.text != "聚合回答：1. 来源A 2. 来源B 3. 来源C" for item in items)
    assert len({item.source_note for item in items}) == 1
