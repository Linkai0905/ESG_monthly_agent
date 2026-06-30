---
name: issue-chain-builder
description: Build auditable ESG issue chains from rule, industry, company, and benchmark-company events.
---

# IssueChainBuilderSkill

Builds evidence chains around material ESG issues.

## When To Use

Runs after event classification and before exposure assessment or recommendation generation.

Research execution, evidence extraction, and report writing are outside this module.

## Inputs

- `state.materiality_topics`
- `state.rule_changes`
- `state.industry_events`
- `state.company_events`
- `state.peer_actions`
- `state.evidence_items`

## Outputs

- `issue_chains: list[IssueChain]`
- Schema: `IssueChainBuilderOutput`
- Runner: `runner.py`

## Execution Contract

1. Each chain organizes available evidence for one material issue.
2. Event IDs and evidence IDs are preserved.
3. Benchmark-company actions are comparison signals, not facts about the report subject.
4. Missing links are explicit.

## Evidence And Failure Rules

- Causal links are not inferred without supporting evidence.
- P2/P3-only sources do not produce evidence-sufficient chains.
- Missing layers produce partial chains with recorded gaps.

## Acceptance Checks

- Output validates as `list[IssueChain]`.
- Each chain links to an issue and traceable event or evidence.
- No report prose is emitted.
