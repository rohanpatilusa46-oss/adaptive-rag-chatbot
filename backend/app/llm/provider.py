from __future__ import annotations

import asyncio
from typing import AsyncIterator, Iterable, List

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.llm.types import ChatCompletionResult, LLMMessage

logger = get_logger(__name__)


class LLMProvider:
    """Abstract LLM provider interface."""

    async def acomplete(
        self,
        messages: List[LLMMessage],
        stream: bool = False,
    ) -> ChatCompletionResult | AsyncIterator[str]:
        raise NotImplementedError


class OpenAILikeProvider(LLMProvider):
    """A minimal provider compatible with OpenAI-style chat APIs.

    For now, if no API key is configured, this falls back to a local echo-style
    implementation so that the rest of the stack is testable without external
    dependencies. This keeps the project usable in demo mode while preserving
    a production-ready abstraction.
    """

    def __init__(self) -> None:
        self._api_key = settings.llm_api_key
        self._api_base = settings.llm_api_base or "https://api.openai.com/v1"
        self._model = settings.llm_model or "gpt-4o-mini"

    async def acomplete(
        self,
        messages: List[LLMMessage],
        stream: bool = False,
    ) -> ChatCompletionResult | AsyncIterator[str]:
        if not self._api_key:
            # Fallback: simple echo-style response for local testing.
            user_content = next((m.content for m in reversed(messages) if m.role == "user"), "")
            content = f"(demo mode) You said: {user_content}"
            if stream:
                return self._fake_stream(content)
            return ChatCompletionResult(content=content)

        if stream:
            return self._stream_from_api(messages)

        return await self._call_api(messages)

    async def _call_api(self, messages: List[LLMMessage]) -> ChatCompletionResult:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(base_url=self._api_base, timeout=30) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        return ChatCompletionResult(content=content)

    async def _stream_from_api(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(base_url=self._api_base, timeout=None) as client:
            async with client.stream("POST", "/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            chunk = line[len("data: ") :]
                            data = httpx.Response(200, text=chunk).json()
                        except Exception:
                            continue
                        delta = data["choices"][0]["delta"].get("content")
                        if delta:
                            yield delta

    async def _fake_stream(self, content: str) -> AsyncIterator[str]:
        for token in content.split():
            yield token + " "
            await asyncio.sleep(0)


def get_llm_provider() -> LLMProvider:
    return OpenAILikeProvider()

