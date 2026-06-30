---
name: decide-research-next-step
description: Decide the next hosted research action from a DeepSearch reflection. Use after ReflectDeepSearchSkill to accept evidence, request another round, switch provider, or give up at max rounds.
---

# DecideResearchNextStepSkill

Choose the next action for the hosted DeepSearch loop.

## When To Use

Use this skill after `ReflectDeepSearchSkill` evaluates a hosted result.

Do not use it before a result and reflection exist.

## Inputs

- `task: DeepSearchTask`
- `result: DeepSearchResult`
- `reflection: ReflectionResult`
- `current_round: int`
- `max_rounds: int`

## Outputs

- `ResearchDecision`
- Schema export: `ResearchDecision` in `schema.py`
- Runner: `runner.py`

## Execution Contract

1. Return `enough` when reflection says the result passed all quality gates.
2. Return `give_up` when the max research rounds have been reached before quality is sufficient.
3. Return `switch_provider` when reflection recommends a different provider for official-domain confirmation.
4. Otherwise return `need_more` with a refined follow-up task.
5. Preserve missing evidence and stop conditions for auditability.

## Evidence And Failure Rules

- Do not accept weak evidence just to stop the loop early.
- Do not exceed `max_rounds`.
- Do not create factual evidence in this skill; only decide the next research action.

## Acceptance Checks

- Output validates as `ResearchDecision`.
- Decision action is one of `enough`, `need_more`, `switch_provider`, or `give_up`.
- Output contains no final report markdown.
