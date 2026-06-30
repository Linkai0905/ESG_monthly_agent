from __future__ import annotations

from esg_monthly_agent.research_providers.anthropic_web_search_provider import (
    AnthropicWebSearchProvider,
)
from esg_monthly_agent.research_providers.base import (
    DeepSearchProvider,
    ProviderConfigurationError,
    ProviderRuntimeError,
)
from esg_monthly_agent.research_providers.local_vector_provider import LocalVectorProvider
from esg_monthly_agent.research_providers.openai_deep_research_provider import (
    OpenAIDeepResearchProvider,
)
from esg_monthly_agent.research_providers.openai_web_search_provider import (
    OpenAIWebSearchProvider,
)
from esg_monthly_agent.research_providers.qwen_dashscope_search_provider import (
    QwenDashScopeSearchProvider,
)
from esg_monthly_agent.research_providers.tavily_official_search_provider import (
    TavilyOfficialSearchProvider,
)
from esg_monthly_agent.research_providers.zhipu_web_search_provider import (
    ZhipuWebSearchProvider,
)


def get_research_provider(name: str) -> DeepSearchProvider:
    providers = {
        "openai_web_search": OpenAIWebSearchProvider,
        "openai_deep_research": OpenAIDeepResearchProvider,
        "anthropic_web_search": AnthropicWebSearchProvider,
        "qwen_dashscope_search": QwenDashScopeSearchProvider,
        "zhipu_web_search": ZhipuWebSearchProvider,
        "zhipu_glm_web_search": ZhipuWebSearchProvider,
        "tavily_official_search": TavilyOfficialSearchProvider,
        "local_vector": LocalVectorProvider,
    }
    try:
        return providers[name]()
    except KeyError as exc:
        raise ProviderConfigurationError(f"Unknown research provider: {name}") from exc


__all__ = [
    "AnthropicWebSearchProvider",
    "DeepSearchProvider",
    "LocalVectorProvider",
    "OpenAIDeepResearchProvider",
    "OpenAIWebSearchProvider",
    "ProviderConfigurationError",
    "ProviderRuntimeError",
    "QwenDashScopeSearchProvider",
    "TavilyOfficialSearchProvider",
    "ZhipuWebSearchProvider",
    "get_research_provider",
]
