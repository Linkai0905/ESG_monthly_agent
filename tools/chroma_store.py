from __future__ import annotations


class ChromaStoreTool:
    name = "chroma_store"

    def add(self, documents: list[dict]) -> int:
        return len(documents)

    def search(self, query: str, k: int = 5) -> list[dict]:
        return []
