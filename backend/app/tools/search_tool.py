from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.search.tavily_client import get_search_provider
from app.schemas.tool import SearchToolInput, SearchToolOutput
from app.tools.base import Tool


class SearchTool(Tool[SearchToolInput, SearchToolOutput]):
    name = "search_web"
    description = "Searches the web for up-to-date information and relevant sources."
    input_model = SearchToolInput
    output_model = SearchToolOutput

    def __init__(self, db: AsyncSession | None = None) -> None:
        super().__init__(db=db)
        self._provider = get_search_provider()

    async def _execute(self, parsed_input: SearchToolInput) -> SearchToolOutput:
        results = await self._provider.search(
            query=parsed_input.query,
            max_results=parsed_input.max_results,
        )
        return SearchToolOutput(query=parsed_input.query, results=results)

