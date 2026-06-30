from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_FILES = sorted((ROOT / "skills").glob("*/*/SKILL.md"))

REQUIRED_SECTIONS = [
    "## When To Use",
    "## Inputs",
    "## Outputs",
    "## Execution Contract",
    "## Evidence And Failure Rules",
    "## Acceptance Checks",
]

FORBIDDEN_LEGACY_PHRASES = [
    "客户",
    "目标公司",
    "建议必须包含",
    "不允许把新闻摘要直接当作 ESG 建议",
    "本步骤",
    "输入企业",
]


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n")
    end = text.find("\n---\n", 4)
    assert end != -1
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        if key and value:
            fields[key.strip()] = value.strip()
    return fields


def test_all_skill_contracts_are_structured() -> None:
    assert len(SKILL_FILES) == 23
    names = []
    for path in SKILL_FILES:
        text = path.read_text(encoding="utf-8")
        fields = _frontmatter(text)
        assert fields.get("name"), path
        assert fields.get("description"), path
        names.append(fields["name"])
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{path} missing {section}"
    assert len(names) == len(set(names))


def test_skill_contracts_do_not_regress_to_legacy_wording() -> None:
    for path in SKILL_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in FORBIDDEN_LEGACY_PHRASES:
            assert phrase not in text, f"{path} contains legacy phrase {phrase!r}"
