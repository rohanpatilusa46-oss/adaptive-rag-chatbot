from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, Dict, Generic, Tuple, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.tool_log import ToolLog


InputModelT = TypeVar("InputModelT", bound=BaseModel)
OutputModelT = TypeVar("OutputModelT", bound=BaseModel)

logger = get_logger(__name__)


class Tool(ABC, Generic[InputModelT, OutputModelT]):
    """Abstract base class for tools used by the agent."""

    name: str
    description: str
    input_model: Type[InputModelT]
    output_model: Type[OutputModelT]

    def __init__(self, db: AsyncSession | None = None) -> None:
        self._db = db

    async def run(
        self,
        raw_input: Dict[str, Any],
        conversation_id: str | None = None,
    ) -> Tuple[OutputModelT, int]:
        """Validate input, execute tool, and log usage.

        Returns (output_model, latency_ms).
        """
        parsed_input = self.input_model(**raw_input)
        start = perf_counter()
        output = await self._execute(parsed_input)
        latency_ms = int((perf_counter() - start) * 1000)

        await self._log_tool_call(
            conversation_id=conversation_id,
            tool_name=self.name,
            tool_input=parsed_input.model_dump(),
            tool_output=output.model_dump(),
            latency_ms=latency_ms,
        )

        return output, latency_ms

    @abstractmethod
    async def _execute(self, parsed_input: InputModelT) -> OutputModelT:
        """Implement the core tool behavior."""

    async def _log_tool_call(
        self,
        conversation_id: str | None,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Dict[str, Any],
        latency_ms: int,
    ) -> None:
        """Persist tool call metadata if a DB session is available."""
        if self._db is None:
            logger.info(
                "tool_call",
                tool_name=tool_name,
                conversation_id=conversation_id,
                latency_ms=latency_ms,
            )
            return

        log = ToolLog(
            conversation_id=None if conversation_id is None else conversation_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            latency_ms=latency_ms,
        )
        self._db.add(log)
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            logger.exception("Failed to persist tool log", tool_name=tool_name)

