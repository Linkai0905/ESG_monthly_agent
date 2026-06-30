from __future__ import annotations

from bs4 import BeautifulSoup


class HTMLParserTool:
    name = "html_parser"

    def invoke(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
