from __future__ import annotations

from typing import List

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.search.base import SearchProvider
from app.schemas.tool import SearchResult

logger = get_logger(__name__)


class TavilySearchProvider(SearchProvider):
    """Tavily-backed search provider abstraction."""

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        api_key = settings.search_api_key
        if not api_key:
            # Fallback demo behavior when no API key is configured.
            logger.info("tavily_demo_mode", query=query)
            return [
                SearchResult(
                    title="Demo search result",
                    url="https://example.com",
                    snippet=f"(demo mode) Search for: {query}",
                    content=None,
                )
            ]

        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }

        async with httpx.AsyncClient(base_url=settings.search_api_base, timeout=20) as client:
            resp = await client.post("/search", json=payload)
            resp.raise_for_status()
            data = resp.json()

        results: List[SearchResult] = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title") or "Untitled",
                    url=item.get("url") or "",
                    snippet=item.get("snippet") or "",
                    content=item.get("content"),
                )
            )
        return results


def get_search_provider() -> SearchProvider:
    return TavilySearchProvider()

