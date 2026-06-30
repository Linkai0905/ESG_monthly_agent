from __future__ import annotations


def run(state: dict) -> dict:
    records = state.get("source_records", [])
    warnings = []
    low_authority = [record for record in records if record.get("priority") in {"P2", "P3"}]
    if low_authority:
        warnings.append(
            {
                "stage": "source_quality_filter",
                "message": f"Flagged {len(low_authority)} P2/P3 sources; do not use them alone for high-risk conclusions.",
            }
        )
    return {"warnings": warnings}
