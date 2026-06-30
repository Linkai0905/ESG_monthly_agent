from __future__ import annotations

import os
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


class WebSearchTool:
    """Web search adapter with API and lightweight HTML fallback.

    If `ESG_SEARCH_API_URL` is set, the tool calls it with `q=<query>` and
    expects either a list of result dicts or `{"results": [...]}`. Without an
    API, it performs a best-effort DuckDuckGo HTML request. Production runs
    should prefer a stable search API.
    """

    name = "web_search"

    def invoke(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        api_url = os.getenv("ESG_SEARCH_API_URL")
        if api_url:
            return self._api_search(api_url, query, top_k)
        return self._duckduckgo_html_search(query, top_k)

    def _api_search(self, api_url: str, query: str, top_k: int) -> list[dict]:
        response = requests.get(api_url, params={"q": query, "top_k": top_k}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", payload) if isinstance(payload, dict) else payload
        return [self._normalize_result(item, query) for item in results[:top_k]]

    def _duckduckgo_html_search(self, query: str, top_k: int) -> list[dict]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(url, timeout=20, headers={"User-Agent": "esg-monthly-agent/0.1"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict] = []
        for result in soup.select(".result"):
            link = result.select_one(".result__a")
            if not link:
                continue
            snippet = result.select_one(".result__snippet")
            href = link.get("href") or ""
            results.append(
                {
                    "title": link.get_text(" ", strip=True),
                    "url": href,
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                    "publisher": "",
                    "publish_date": None,
                    "query": query,
                }
            )
            if len(results) >= top_k:
                break
        return results

    def _normalize_result(self, item: dict, query: str) -> dict:
        return {
            "title": item.get("title") or item.get("name") or "",
            "url": item.get("url") or item.get("link") or "",
            "snippet": item.get("snippet") or item.get("summary") or item.get("description") or "",
            "publisher": item.get("publisher") or item.get("source") or "",
            "publish_date": item.get("publish_date") or item.get("date"),
            "query": item.get("query") or query,
        }
