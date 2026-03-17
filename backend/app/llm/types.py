from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

LLMRole = Literal["user", "assistant", "system", "tool"]


@dataclass
class LLMMessage:
    role: LLMRole
    content: str


@dataclass
class ChatCompletionResult:
    """Simplified result for a non-streaming chat completion."""

    content: str
    # In later phases we can add tool calls, citations, etc.

