from __future__ import annotations


async def get_langchain_docs_tools():
    """Load LangChain docs MCP tools for implementation assistance only."""

    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(
        {
            "docs-langchain": {
                "transport": "http",
                "url": "https://docs.langchain.com/mcp",
            }
        }
    )
    return await client.get_tools()
