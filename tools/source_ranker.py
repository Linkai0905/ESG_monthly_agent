from __future__ import annotations


class SourceRankerTool:
    name = "source_ranker"

    def invoke(self, candidates: list[dict]) -> list[dict]:
        return sorted(
            candidates,
            key=lambda item: (
                item.get("authority_score", 0),
                item.get("relevance_score", 0),
                item.get("freshness_score", 0),
            ),
            reverse=True,
        )
