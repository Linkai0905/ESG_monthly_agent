from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from esg_monthly_agent.config import PROJECT_ROOT


class EvidenceStoreTool:
    name = "evidence_store"

    def save_json(self, path: str | Path, data) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(target)

    def init_db(self, path: str | Path | None = None) -> str:
        target = Path(path) if path else PROJECT_ROOT / "storage" / "evidence.sqlite"
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_items (
                    evidence_id TEXT PRIMARY KEY,
                    issue_ids TEXT NOT NULL,
                    layer TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    publisher TEXT NOT NULL,
                    publish_date TEXT,
                    source_priority TEXT,
                    authority_score REAL,
                    freshness_score REAL,
                    relevance_score REAL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_issue_layer ON evidence_items(issue_ids, layer)"
            )
        return str(target)

    def upsert_evidence_items(
        self,
        items: list[dict[str, Any]],
        path: str | Path | None = None,
        replace_existing: bool = True,
    ) -> str:
        target = Path(self.init_db(path))
        with sqlite3.connect(target) as conn:
            if replace_existing:
                conn.execute("DELETE FROM evidence_items")
            conn.executemany(
                """
                INSERT INTO evidence_items (
                    evidence_id, issue_ids, layer, source_url, source_title, publisher,
                    publish_date, source_priority, authority_score, freshness_score,
                    relevance_score, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                    issue_ids=excluded.issue_ids,
                    layer=excluded.layer,
                    source_url=excluded.source_url,
                    source_title=excluded.source_title,
                    publisher=excluded.publisher,
                    publish_date=excluded.publish_date,
                    source_priority=excluded.source_priority,
                    authority_score=excluded.authority_score,
                    freshness_score=excluded.freshness_score,
                    relevance_score=excluded.relevance_score,
                    payload_json=excluded.payload_json
                """,
                [
                    (
                        item["evidence_id"],
                        ",".join(item.get("related_issues", [])),
                        item.get("layer", ""),
                        item.get("source_url", ""),
                        item.get("source_title", ""),
                        item.get("publisher", ""),
                        item.get("publish_date"),
                        item.get("source_priority"),
                        item.get("authority_score"),
                        item.get("freshness_score"),
                        item.get("relevance_score"),
                        json.dumps(item, ensure_ascii=False),
                    )
                    for item in items
                ],
            )
        return str(target)
