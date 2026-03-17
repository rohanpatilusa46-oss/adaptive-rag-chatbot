from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.memory import MemoryEntry
from app.repositories.memory_repository import MemoryRepository
from app.schemas.tool import (
    GetMemoryInput,
    GetMemoryOutput,
    MemoryEntrySchema,
    SaveMemoryInput,
    SaveMemoryOutput,
)


class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = MemoryRepository(db)

    async def save_memory(self, payload: SaveMemoryInput) -> SaveMemoryOutput:
        entry = await self._repo.add_entry(
            user_id=payload.user_id,
            key=payload.key,
            value=payload.value,
            category=payload.category,
        )
        return SaveMemoryOutput(success=True, memory_id=str(entry.id))

    async def get_memory(self, payload: GetMemoryInput) -> GetMemoryOutput:
        entries: List[MemoryEntry] = await self._repo.list_entries(user_id=payload.user_id)
        return GetMemoryOutput(
            entries=[
                MemoryEntrySchema(
                    id=str(e.id),
                    key=e.key,
                    value=e.value,
                    category=e.category,
                )
                for e in entries
            ]
        )

