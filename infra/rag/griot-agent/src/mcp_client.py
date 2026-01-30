"""FastMCP client wrapper for retrieval-mcp server."""

import asyncio
from typing import Any

from fastmcp import Client

from .config import get_settings


class RetrievalMCPClient:
    """Client for the retrieval-mcp server using FastMCP."""

    def __init__(self, url: str | None = None):
        """Initialize the client.

        Args:
            url: MCP server URL. Defaults to settings.retrieval_mcp_url.
        """
        settings = get_settings()
        self.url = url or settings.retrieval_mcp_url
        self._client: Client | None = None

    async def __aenter__(self):
        """Enter async context."""
        self._client = Client(self.url)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""
        if not self._client:
            raise RuntimeError("Client not connected. Use async with context.")
        tools = await self._client.list_tools()
        return [{"name": t.name, "description": t.description} for t in tools]

    async def search(
        self,
        query: str,
        collection: str | None = None,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> dict[str, Any]:
        """Search the vector database.

        Args:
            query: Search query text
            collection: Collection name (defaults to 'griot')
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            Search results with documents and metadata
        """
        if not self._client:
            raise RuntimeError("Client not connected. Use async with context.")

        settings = get_settings()
        collection = collection or settings.default_collection

        result = await self._client.call_tool(
            "rag_search",
            {
                "query": query,
                "collection": collection,
                "top_k": top_k,
                "score_threshold": score_threshold,
            },
        )
        return result

    async def list_collections(self) -> dict[str, Any]:
        """List available collections."""
        if not self._client:
            raise RuntimeError("Client not connected. Use async with context.")

        result = await self._client.call_tool("rag_list_collections", {})
        return result

    async def list_sources(self, collection: str | None = None) -> dict[str, Any]:
        """List sources in a collection.

        Args:
            collection: Collection name (defaults to 'griot')

        Returns:
            List of source documents in the collection
        """
        if not self._client:
            raise RuntimeError("Client not connected. Use async with context.")

        settings = get_settings()
        collection = collection or settings.default_collection

        result = await self._client.call_tool(
            "rag_list_sources",
            {"collection": collection},
        )
        return result

    async def rewrite_query(
        self,
        query: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Rewrite a query for better retrieval.

        Args:
            query: Original query
            context: Optional conversation context

        Returns:
            Rewritten query optimized for retrieval
        """
        if not self._client:
            raise RuntimeError("Client not connected. Use async with context.")

        params = {"query": query}
        if context:
            params["context"] = context

        result = await self._client.call_tool("rag_rewrite_query", params)
        return result


async def test_connection():
    """Test the MCP client connection."""
    async with RetrievalMCPClient() as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        return tools


if __name__ == "__main__":
    asyncio.run(test_connection())
