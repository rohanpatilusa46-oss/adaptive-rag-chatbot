from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.schemas.tool import SearchResult


class SearchProvider(ABC):
    """Abstract interface for web search providers."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError

