from __future__ import annotations

import asyncio

from esg_monthly_agent.research_providers.anthropic_web_search_provider import (
    AnthropicWebSearchProvider,
)
from esg_monthly_agent.research_providers.base import DeepSearchProvider
from esg_monthly_agent.research_providers.openai_web_search_provider import (
    OpenAIWebSearchProvider,
)
from esg_monthly_agent.research_providers.qwen_dashscope_search_provider import (
    QwenDashScopeSearchProvider,
)
from esg_monthly_agent.research_providers.tavily_official_search_provider import (
    TavilyOfficialSearchProvider,
)
from esg_monthly_agent.research_providers.zhipu_web_search_provider import (
    ZhipuWebSearchProvider,
)
from esg_monthly_agent.schemas.deepsearch import DeepSearchResult, DeepSearchTask


class FakeResponse:
    status_code = 200
    text = "ok"

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def _task() -> DeepSearchTask:
    return DeepSearchTask(
        task_id="deep_task",
        issue_id="mine_safety",
        layer="company",
        object_type="CompanyEvent",
        company="中国神华",
        period={"label": "2026-06"},
        research_goal="研究公司公告",
        initial_question="检索公司公告",
        required_evidence=["公司公告"],
        source_policy={},
        allowed_domains=["shenhuachina.com", "sse.com.cn", "hkexnews.hk"],
        expected_output_schema="CompanyEvent",
    )


def test_openai_web_search_provider_returns_deepsearch_result():
    payload = {
        "output": [
            {
                "type": "web_search_call",
                "status": "completed",
                "action": {
                    "query": "中国神华 公告",
                    "sources": [
                        {
                            "title": "中国神华公告",
                            "url": "https://www.shenhuachina.com/news",
                            "publisher": "中国神华",
                        }
                    ],
                },
            },
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "中国神华发布公告。", "annotations": []}],
            },
        ]
    }
    provider: DeepSearchProvider = OpenAIWebSearchProvider(api_key="test", post=lambda *a, **k: FakeResponse(payload))

    result = asyncio.run(provider.research(_task()))

    assert isinstance(result, DeepSearchResult)
    assert result.status == "completed"
    assert result.citations


def test_anthropic_web_search_provider_returns_deepsearch_result():
    payload = {
        "content": [
            {
                "type": "web_search_tool_result",
                "content": [
                    {
                        "title": "中国神华公告",
                        "url": "https://www.shenhuachina.com/news",
                        "publisher": "中国神华",
                    }
                ],
            },
            {"type": "text", "text": "中国神华发布公告。"},
        ]
    }
    provider: DeepSearchProvider = AnthropicWebSearchProvider(api_key="test", post=lambda *a, **k: FakeResponse(payload))

    result = asyncio.run(provider.research(_task()))

    assert isinstance(result, DeepSearchResult)
    assert result.status == "completed"
    assert result.citations


def test_qwen_dashscope_search_provider_returns_deepsearch_result():
    calls = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse(payload)

    payload = {
        "request_id": "req-test",
        "output": {
            "text": "中国神华发布公告。",
            "search_info": {
                "search_results": [
                    {
                        "title": "中国神华公告",
                        "url": "https://www.shenhuachina.com/news",
                        "site_name": "中国神华",
                        "snippet": "公告片段",
                    }
                ]
            },
        },
        "usage": {"total_tokens": 100},
    }
    provider: DeepSearchProvider = QwenDashScopeSearchProvider(
        api_key="test", search_strategy="turbo", post=fake_post
    )

    result = asyncio.run(provider.research(_task()))

    assert isinstance(result, DeepSearchResult)
    assert result.status == "completed"
    assert result.provider == "qwen_dashscope_search"
    assert result.citations[0].url == "https://www.shenhuachina.com/news"
    request_payload = calls[0]["kwargs"]["json"]
    assert request_payload["parameters"]["enable_search"] is True
    assert request_payload["parameters"]["result_format"] == "message"
    assert request_payload["parameters"]["search_options"]["enable_source"] is True
    assert request_payload["parameters"]["search_options"]["enable_citation"] is True
    assert request_payload["parameters"]["search_options"]["search_strategy"] == "turbo"


def test_zhipu_web_search_provider_returns_deepsearch_result():
    calls = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse(payload)

    payload = {
        "request_id": "req-zhipu",
        "search_result": [
            {
                "title": "中国神华公告",
                "link": "https://www.shenhuachina.com/news",
                "media": "中国神华",
                "publish_date": "2026-06-18",
                "content": "公告片段",
            }
        ],
    }
    provider: DeepSearchProvider = ZhipuWebSearchProvider(
        api_key="test",
        api_url="https://open.bigmodel.cn/api/paas/v4/web_search",
        search_engine="search_pro",
        count=10,
        post=fake_post,
    )

    result = asyncio.run(provider.research(_task()))

    assert isinstance(result, DeepSearchResult)
    assert result.status == "completed"
    assert result.provider == "zhipu_web_search"
    assert result.citations[0].url == "https://www.shenhuachina.com/news"
    assert result.citations[0].publisher == "中国神华"
    request_payload = calls[0]["kwargs"]["json"]
    assert len(calls) > 1
    assert request_payload["search_engine"] == "search_pro"
    assert request_payload["count"] <= 5
    assert request_payload["content_size"] == "high"
    assert "site:shenhuachina.com" in request_payload["search_query"]


def test_zhipu_openai_compatible_gateway_returns_deepsearch_result():
    calls = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse(payload)

    payload = {
        "id": "chatcmpl-zhipu-compatible",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"answer":"中国神华发布公告。","sources":[{'
                        '"title":"中国神华公告",'
                        '"url":"https://www.shenhuachina.com/news",'
                        '"publisher":"中国神华",'
                        '"publish_date":"2026-06-18",'
                        '"snippet":"公告片段"}]}'
                    )
                }
            }
        ],
        "usage": {"total_tokens": 100},
    }
    provider: DeepSearchProvider = ZhipuWebSearchProvider(
        api_key="test",
        api_url="https://glm-compatible.example/v1",
        model="glm-5.2",
        post=fake_post,
    )

    result = asyncio.run(provider.research(_task()))

    assert isinstance(result, DeepSearchResult)
    assert result.status == "completed"
    assert result.provider == "zhipu_web_search"
    assert result.citations[0].url == "https://www.shenhuachina.com/news"
    assert result.citations[0].snippet_or_quote == "公告片段"
    assert calls[0]["args"][0] == "https://glm-compatible.example/v1/chat/completions"
    request_payload = calls[0]["kwargs"]["json"]
    assert request_payload["model"] == "glm-5.2"
    assert "site:shenhuachina.com" in request_payload["messages"][1]["content"]


def test_zhipu_web_search_provider_filters_non_allowed_domains_from_citations():
    payload = {
        "request_id": "req-zhipu",
        "search_result": [
            {
                "title": "媒体转载",
                "link": "https://news.qq.com/rain/a/test",
                "media": "腾讯新闻",
                "publish_date": "2026-06-18",
                "content": "媒体片段",
            }
        ],
    }
    provider: DeepSearchProvider = ZhipuWebSearchProvider(
        api_key="test",
        api_url="https://open.bigmodel.cn/api/paas/v4/web_search",
        search_engine="search_pro",
        count=10,
        post=lambda *a, **k: FakeResponse(payload),
    )

    result = asyncio.run(provider.research(_task()))

    assert result.status == "partial"
    assert not result.citations
    assert result.claims[0].claim_type == "inference"
    assert "second official-source confirmation" in " ".join(result.uncertainty)


def test_tavily_official_search_provider_uses_include_domains():
    calls = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse(payload)

    payload = {
        "results": [
            {
                "title": "中国神华公告",
                "url": "https://www.shenhuachina.com/news",
                "content": "公告片段",
                "published_date": "2026-06-18",
            },
            {
                "title": "媒体转载",
                "url": "https://news.qq.com/rain/a/test",
                "content": "媒体片段",
                "published_date": "2026-06-18",
            },
        ]
    }
    provider: DeepSearchProvider = TavilyOfficialSearchProvider(
        api_key="test",
        search_depth="advanced",
        max_results=5,
        post=fake_post,
    )

    result = asyncio.run(provider.research(_task()))

    assert isinstance(result, DeepSearchResult)
    assert result.status == "completed"
    assert result.provider == "tavily_official_search"
    assert [item.url for item in result.citations] == ["https://www.shenhuachina.com/news"]
    assert len(result.claims) == 1
    assert result.claims[0].text == "公告片段"
    assert result.claims[0].citation_ids == [result.citations[0].citation_id]
    request_payload = calls[0]["kwargs"]["json"]
    assert request_payload["include_domains"] == ["shenhuachina.com", "sse.com.cn", "hkexnews.hk"]
    assert request_payload["search_depth"] == "advanced"


def test_tavily_official_search_provider_filters_generic_list_pages():
    payload = {
        "results": [
            {
                "title": "ESG动态 - 中国神华",
                "url": "http://www.shenhuachina.com/zgshww/xesgdt/shzrlist1.shtml",
                "content": "首页 关于我们 新闻中心 投资者关系 联系我们 网站地图",
                "published_date": "2026-06-18",
            },
            {
                "title": "中国神华安全生产公告",
                "url": "https://www.shenhuachina.com/news/20260618.shtml",
                "content": "中国神华披露安全生产相关进展。",
                "published_date": "2026-06-18",
            },
        ]
    }
    provider: DeepSearchProvider = TavilyOfficialSearchProvider(
        api_key="test",
        search_depth="advanced",
        max_results=5,
        post=lambda *args, **kwargs: FakeResponse(payload),
    )

    result = asyncio.run(provider.research(_task()))

    assert [item.url for item in result.citations] == ["https://www.shenhuachina.com/news/20260618.shtml"]
    assert result.source_coverage["filtered_non_official"] == 1
