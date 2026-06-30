from __future__ import annotations

import os

from esg_monthly_agent.config import OPENAI_DEEP_RESEARCH_ENABLED, OPENAI_DEEP_RESEARCH_MODEL
from esg_monthly_agent.research_providers.base import ProviderConfigurationError
from esg_monthly_agent.research_providers.openai_web_search_provider import OpenAIWebSearchProvider
from esg_monthly_agent.schemas.deepsearch import DeepSearchResult, DeepSearchTask


class OpenAIDeepResearchProvider:
    name = "openai_deep_research"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    async def research(self, task: DeepSearchTask) -> DeepSearchResult:
        if not OPENAI_DEEP_RESEARCH_ENABLED:
            raise ProviderConfigurationError(
                "OpenAI Deep Research provider is not configured or not available. "
                "Use openai_web_search or anthropic_web_search instead."
            )
        if not self.api_key:
            raise ProviderConfigurationError("OpenAI Deep Research requires OPENAI_API_KEY.")
        return await OpenAIWebSearchProvider(
            api_key=self.api_key,
            model=OPENAI_DEEP_RESEARCH_MODEL,
        ).research(task)
