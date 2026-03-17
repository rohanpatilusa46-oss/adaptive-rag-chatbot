from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.tool import (
    GetMemoryInput,
    GetMemoryOutput,
    SaveMemoryInput,
    SaveMemoryOutput,
)
from app.services.memory_service import MemoryService
from app.tools.base import Tool


class SaveMemoryTool(Tool[SaveMemoryInput, SaveMemoryOutput]):
    name = "save_memory"
    description = "Stores a user-specific fact or preference in long-term memory."
    input_model = SaveMemoryInput
    output_model = SaveMemoryOutput

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db=db)
        self._service = MemoryService(db)

    async def _execute(self, parsed_input: SaveMemoryInput) -> SaveMemoryOutput:
        return await self._service.save_memory(parsed_input)


class GetMemoryTool(Tool[GetMemoryInput, GetMemoryOutput]):
    name = "get_memory"
    description = "Retrieves all known long-term memory entries for the given user."
    input_model = GetMemoryInput
    output_model = GetMemoryOutput

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db=db)
        self._service = MemoryService(db)

    async def _execute(self, parsed_input: GetMemoryInput) -> GetMemoryOutput:
        return await self._service.get_memory(parsed_input)

