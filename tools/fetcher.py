from __future__ import annotations

import requests


class FetcherTool:
    name = "fetcher"

    def invoke(self, url: str, timeout: int = 20) -> dict:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "esg-monthly-agent/0.1"})
        response.raise_for_status()
        return {
            "url": url,
            "content_type": response.headers.get("content-type", ""),
            "text": response.text,
            "bytes": response.content,
        }
