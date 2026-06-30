---
name: report-writer
description: Write the final ESG monthly markdown report from structured evidence-backed objects only. This is the only module that emits report_markdown.
---

# ReportWriterSkill

Assembles evidence, events, issue chains, exposures, and recommendations into the final Markdown report.

## When To Use

Runs after classification, issue-chain building, exposure assessment, recommendations, and quality checks.

Source collection, new factual claims, and evidence-chain mutation are outside this module.

## Inputs

- `state.report_contract`
- `state.rule_changes`
- `state.industry_events`
- `state.company_events`
- `state.peer_actions`
- `state.issue_chains`
- `state.company_exposures`
- `state.recommendations`
- `state.evidence_items`
- `state.quality_checks`

## Outputs

- `report_sections: dict[str, ReportSection]`
- `report_markdown: str`
- Schema: `ReportWriterOutput`
- Runner: `runner.py`

## Execution Contract

1. Final prose is emitted only by this module.
2. Section structure follows `ReportContract`.
3. The default scenario is a China Shenhua ESG monthly report; other companies follow initialized state.
4. Factual bullets and recommendations preserve evidence references where available.
5. Benchmark-company actions are presented as comparison signals.

## Evidence And Failure Rules

- No new facts are introduced outside structured state.
- Evidence gaps and weak-source limits remain visible.
- Report-facing wording names the configured report subject and does not expose compatibility-key wording.

## Acceptance Checks

- Output validates as `ReportWriterOutput`.
- Markdown contains the required monthly-report sections.
- Evidence-backed factual bullets contain evidence references.
