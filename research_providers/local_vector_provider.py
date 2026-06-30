from __future__ import annotations

from esg_monthly_agent.schemas.deepsearch import DeepSearchResult, DeepSearchTask


class LocalVectorProvider:
    name = "local_vector"

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        return DeepSearchResult(
            task_id=task.task_id,
            issue_id=task.issue_id,
            provider=self.name,
            status="failed",
            answer_summary="Local vector provider is reserved for local/manual corpus mode.",
            missing_evidence=["Local vector research is not realtime web research."],
            uncertainty=["Use source_mode=local or ingest local files before local vector research."],
            confidence=0.0,
        )
