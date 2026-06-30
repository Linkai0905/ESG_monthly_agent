from __future__ import annotations

try:
    from esg_monthly_agent.tools.web_search import WebSearchTool
except ModuleNotFoundError:  # pragma: no cover - direct module debugging from package dir
    from .web_search import WebSearchTool


class NewsSearchTool:
    name = "news_search"

    def invoke(self, query: str, **kwargs) -> list[dict]:
        news_query = f"{query} 新闻 OR 公告"
        return WebSearchTool().invoke(news_query, **kwargs)


class CompanyAnnouncementSearchTool:
    name = "company_announcement_search"

    def invoke(self, query: str, company_domain: str | None = None, **kwargs) -> list[dict]:
        site_part = f" site:{company_domain}" if company_domain else ""
        return WebSearchTool().invoke(f"{query} 公告 官网{site_part}", **kwargs)


class ExchangeDisclosureSearchTool:
    name = "exchange_disclosure_search"

    def invoke(self, query: str, **kwargs) -> list[dict]:
        exchange_query = f"{query} site:sse.com.cn OR site:hkexnews.hk 公告"
        return WebSearchTool().invoke(exchange_query, **kwargs)
