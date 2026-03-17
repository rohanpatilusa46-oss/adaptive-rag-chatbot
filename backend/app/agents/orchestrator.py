from __future__ import annotations

from typing import AsyncIterator, List, Optional

from app.llm.prompts import get_system_prompt
from app.llm.provider import LLMProvider, get_llm_provider
from app.llm.types import LLMMessage


class ChatOrchestrator:
    """Core orchestration logic for chat.

    Phase 4: simple single-step LLM call (no tools yet).
    Later phases will add:
    - tool-decision step
    - web search + memory tools
    - grounded answer generation with citations
    """

    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        self._provider = provider or get_llm_provider()

    async def run_chat(
        self,
        user_message: str,
        history: Optional[List[LLMMessage]] = None,
    ) -> str:
        """Non-streaming chat completion."""
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=get_system_prompt())
        ]
        if history:
            messages.extend(history)
        messages.append(LLMMessage(role="user", content=user_message))

        result = await self._provider.acomplete(messages, stream=False)
        # Type narrowing: in non-stream mode we always expect ChatCompletionResult
        assert not isinstance(result, AsyncIterator)
        return result.content

    async def stream_chat(
        self,
        user_message: str,
        history: Optional[List[LLMMessage]] = None,
    ) -> AsyncIterator[str]:
        """Streaming chat completion yielding text chunks."""
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=get_system_prompt())
        ]
        if history:
            messages.extend(history)
        messages.append(LLMMessage(role="user", content=user_message))

        stream = await self._provider.acomplete(messages, stream=True)
        assert not isinstance(stream, str)
        async for chunk in stream:
            yield chunk

