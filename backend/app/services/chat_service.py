from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import ChatOrchestrator
from app.llm.types import LLMMessage
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage, Role


class ChatService:
    """Service layer for chat interactions.

    Phase 4: orchestrator wiring without persistence or tools.
    """

    def __init__(self, orchestrator: Optional[ChatOrchestrator] = None) -> None:
        self._orchestrator = orchestrator or ChatOrchestrator()

    async def handle_chat(
        self,
        request: ChatRequest,
        db: AsyncSession,  # noqa: ARG002  # reserved for later persistence layers
    ) -> ChatResponse:
        # Phase 4: no DB-backed history yet
        history: list[LLMMessage] = []

        content = await self._orchestrator.run_chat(
            user_message=request.message,
            history=history,
        )

        # Placeholders; will be real UUIDs from DB in persistence phase
        conversation_id = request.conversation_id or "demo-conversation-id"
        message_id = "demo-message-id"

        message = ChatMessage(
            id=message_id,
            role=Role.ASSISTANT,
            content=content,
            citations=None,
        )

        return ChatResponse(conversation_id=conversation_id, message=message)

