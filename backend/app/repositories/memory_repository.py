from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.memory import MemoryEntry


class MemoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_entry(
        self,
        user_id: str,
        key: str,
        value: str,
        category: str,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            user_id=user_id,
            key=key,
            value=value,
            category=category,
        )
        self._db.add(entry)
        await self._db.commit()
        await self._db.refresh(entry)
        return entry

    async def list_entries(self, user_id: str) -> List[MemoryEntry]:
        stmt = select(MemoryEntry).where(MemoryEntry.user_id == user_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

