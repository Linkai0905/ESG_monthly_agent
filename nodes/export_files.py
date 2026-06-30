from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from esg_monthly_agent.tools.evidence_store import EvidenceStoreTool


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def export_files(state: dict) -> dict:
    run_paths = state.get("run_paths") or {}
    base = Path(run_paths.get("base", "runs/default"))
    reports = Path(run_paths.get("reports", base / "reports"))
    reports.mkdir(parents=True, exist_ok=True)

    paths = {
        "report_markdown": reports / "esg_monthly_report.md",
        "report_final": reports / "report_final.md",
        "evidence_items": base / "evidence_items.json",
        "issue_chains": base / "issue_chains.json",
        "recommendations": base / "recommendations.json",
        "quality_checks": base / "quality_checks.json",
        "llm_review": base / "llm_review.json",
        "deepsearch_tasks": base / "deepsearch_tasks.json",
        "deepsearch_results": base / "deepsearch_results.json",
        "deepsearch_reflections": base / "deepsearch_reflections.json",
        "deepsearch_decisions": base / "deepsearch_decisions.json",
        "deepsearch_rounds": base / "deepsearch_rounds.json",
        "context_bundles": base / "context_bundles.json",
        "missing_evidence": base / "missing_evidence.json",
        "search_tasks": base / "search_tasks.json",
        "evidence_needs": base / "evidence_needs.json",
        "materiality_topics": base / "materiality_topics.json",
        "source_records": base / "source_records.json",
        "parsed_documents": base / "parsed_documents.json",
        "evidence_sqlite": Path(__file__).resolve().parents[1] / "storage" / "evidence.sqlite",
    }

    paths["report_markdown"].write_text(state.get("report_markdown", ""), encoding="utf-8")
    paths["report_final"].write_text(state.get("report_markdown", ""), encoding="utf-8")
    _write_json(paths["evidence_items"], state.get("evidence_items", []))
    _write_json(paths["issue_chains"], state.get("issue_chains", []))
    _write_json(paths["recommendations"], state.get("recommendations", []))
    _write_json(paths["quality_checks"], state.get("quality_checks", {}))
    _write_json(paths["llm_review"], state.get("llm_review", {}))
    _write_json(paths["deepsearch_tasks"], state.get("deepsearch_tasks", []))
    _write_json(paths["deepsearch_results"], state.get("deepsearch_results", []))
    _write_json(paths["deepsearch_reflections"], state.get("deepsearch_reflections", []))
    _write_json(paths["deepsearch_decisions"], state.get("deepsearch_decisions", []))
    _write_json(paths["deepsearch_rounds"], state.get("deepsearch_rounds", []))
    _write_json(paths["context_bundles"], state.get("context_bundles", []))
    _write_json(paths["missing_evidence"], state.get("missing_evidence", []))
    _write_json(paths["search_tasks"], state.get("search_tasks", []))
    _write_json(paths["evidence_needs"], state.get("evidence_needs", []))
    _write_json(paths["materiality_topics"], state.get("materiality_topics", []))
    _write_json(paths["source_records"], state.get("source_records", []))
    _write_json(paths["parsed_documents"], state.get("parsed_documents", []))
    EvidenceStoreTool().upsert_evidence_items(state.get("evidence_items", []), paths["evidence_sqlite"])
    legacy_qwen_review = base / "qwen_review.json"
    if legacy_qwen_review.exists():
        legacy_qwen_review.unlink()

    return {"export_paths": {key: str(value) for key, value in paths.items()}}
