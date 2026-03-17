from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import ChatOrchestrator
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatStreamChunk
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    return ChatService()


def get_orchestrator() -> ChatOrchestrator:
    return ChatOrchestrator()


@router.post("", response_model=ChatResponse, summary="Chat (non-streaming)")
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Synchronous-style chat endpoint returning the full assistant reply."""
    return await service.handle_chat(payload, db=db)


@router.post(
    "/stream",
    response_class=StreamingResponse,
    summary="Chat (streaming)",
)
async def chat_stream(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),  # noqa: ARG001  # reserved for later
    orchestrator: ChatOrchestrator = Depends(get_orchestrator),
) -> StreamingResponse:
    """Streaming chat endpoint yielding incremental response chunks."""

    async def event_stream() -> AsyncIterator[bytes]:
        # Phase 4: no DB-backed history yet
        history: list = []
        async for chunk in orchestrator.stream_chat(
            user_message=payload.message,
            history=history,
        ):
            data = ChatStreamChunk(type="delta", delta=chunk)
            yield (json.dumps(data.model_json()) + "\n").encode("utf-8")
        done = ChatStreamChunk(type="done", delta=None)
        yield (json.dumps(done.model_json()) + "\n").encode("utf-8")

    return StreamingResponse(
        event_stream(),
        media_type="application/jsonl",
    )

