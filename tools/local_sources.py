from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

try:
    from esg_monthly_agent.config import DEFAULT_LOCAL_SOURCE_DIR, DEFAULT_MANUAL_SOURCE_CSV
except ModuleNotFoundError:  # pragma: no cover - direct module debugging from package dir
    from config import DEFAULT_LOCAL_SOURCE_DIR, DEFAULT_MANUAL_SOURCE_CSV


@dataclass(frozen=True)
class LocalSource:
    path: Path | None
    public_url: str
    section_hint: str
    title: str
    publisher: str
    expected_date: str | None
    source_type: str
    priority: int
    tags: list[str]
    text: str
    is_sample_source: bool
    note: str


class LocalManualSourceTool:
    """Read curated local ESG sources for deterministic research execution.

    This is not a business-news MCP source. It is an offline sample corpus used
    to exercise the same issue-aware search/fetch/parse/extract pipeline when
    external search credentials are unavailable.
    """

    name = "local_manual_sources"

    def __init__(
        self,
        source_dir: Path | str = DEFAULT_LOCAL_SOURCE_DIR,
        csv_path: Path | str = DEFAULT_MANUAL_SOURCE_CSV,
    ) -> None:
        self.source_dir = Path(source_dir)
        self.csv_path = Path(csv_path)

    def load(self) -> list[LocalSource]:
        if not self.source_dir.exists():
            return []
        metadata = self._read_metadata()
        sources: list[LocalSource] = []
        for path in sorted(self.source_dir.glob("*/*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            section = path.parent.name
            meta = metadata.get(path.name, {})
            text = self._extract_text(path)
            if not text.strip():
                continue
            sources.append(
                LocalSource(
                    path=path,
                    public_url=meta.get("public_url") or self._extract_public_url(text),
                    section_hint=section,
                    title=meta.get("title") or self._title_from_text_or_path(text, path),
                    publisher=meta.get("publisher") or self._default_publisher(section),
                    expected_date=meta.get("expected_date"),
                    source_type=meta.get("source_type") or path.suffix.lstrip(".").lower(),
                    priority=int(meta.get("priority") or self._default_priority(section)),
                    tags=meta.get("tags") or [],
                    text=text,
                    is_sample_source=self._is_sample_source(text, meta),
                    note=meta.get("note") or "",
                )
            )
        sources.extend(self._load_http_rows_not_backed_by_local_files(metadata))
        return sources

    def _read_metadata(self) -> dict[str, dict]:
        if not self.csv_path.exists():
            return {}
        metadata: dict[str, dict] = {}
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                url = row.get("url") or ""
                basename = Path(unquote(urlparse(url).path)).name
                if not basename:
                    continue
                metadata[basename] = {
                    "public_url": url if url.startswith(("http://", "https://")) else "",
                    "expected_date": row.get("expected_date") or None,
                    "source_type": row.get("source_type_hint") or None,
                    "publisher": row.get("source_name_hint") or None,
                    "title": row.get("tags") or row.get("note") or basename,
                    "priority": row.get("priority") or None,
                    "section_hint": row.get("section_hint") or "",
                    "note": row.get("note") or "",
                    "tags": [
                        item.strip()
                        for item in (row.get("tags") or "").replace("，", ",").split(",")
                        if item.strip()
                    ],
                }
        return metadata

    def _load_http_rows_not_backed_by_local_files(self, metadata: dict[str, dict]) -> list[LocalSource]:
        if not self.csv_path.exists():
            return []
        backed_names = {path.name for path in self.source_dir.glob("*/*") if path.is_file()}
        sources: list[LocalSource] = []
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                url = row.get("url") or ""
                if not url.startswith(("http://", "https://")):
                    continue
                basename = Path(unquote(urlparse(url).path)).name
                if basename in backed_names:
                    continue
                title = row.get("tags") or row.get("note") or basename or url
                note = row.get("note") or ""
                section = row.get("section_hint") or "company"
                text = " ".join(part for part in [title, note] if part)
                sources.append(
                    LocalSource(
                        path=None,
                        public_url=url,
                        section_hint=section,
                        title=title,
                        publisher=row.get("source_name_hint") or self._default_publisher(section),
                        expected_date=row.get("expected_date") or None,
                        source_type=row.get("source_type_hint") or "url",
                        priority=int(row.get("priority") or self._default_priority(section)),
                        tags=[
                            item.strip()
                            for item in (row.get("tags") or "").replace("，", ",").split(",")
                            if item.strip()
                        ],
                        text=text,
                        is_sample_source=False,
                        note=note,
                    )
                )
        return sources

    def _extract_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".html", ".htm"}:
            html = path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        if suffix == ".pdf":
            try:
                from esg_monthly_agent.tools.pdf_parser import PDFParserTool

                return PDFParserTool().invoke(path.read_bytes())
            except Exception:
                return path.stem
        return path.read_text(encoding="utf-8", errors="ignore")

    def _title_from_text_or_path(self, text: str, path: Path) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first_line or path.stem

    def _default_publisher(self, section: str) -> str:
        return {
            "policy": "本地政策样例",
            "industry": "本地行业样例",
            "company": "本地公司样例",
            "peer": "本地对标样例",
        }.get(section, "本地样例")

    def _default_priority(self, section: str) -> int:
        return {"policy": 5, "company": 4, "industry": 3, "peer": 3}.get(section, 2)

    def _extract_public_url(self, text: str) -> str:
        match = re.search(r"https?://[^\s)）]+", text or "")
        return match.group(0) if match else ""

    def _is_sample_source(self, text: str, meta: dict) -> bool:
        joined = " ".join(
            [
                text or "",
                meta.get("publisher") or "",
                meta.get("title") or "",
                meta.get("note") or "",
            ]
        )
        sample_markers = ["本地样例", "验收样例", "链路验收", "用于测试", "用于检验", "MVP 验收"]
        return any(marker in joined for marker in sample_markers)
