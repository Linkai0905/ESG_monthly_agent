from __future__ import annotations

from esg_monthly_agent.tools.docs_mcp import get_langchain_docs_tools


class ImplementationHelperAgent:
    """Optional helper for LangChain/LangGraph docs lookup via MCP."""

    async def load_tools(self):
        return await get_langchain_docs_tools()
