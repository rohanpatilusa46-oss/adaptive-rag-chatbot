from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Citation(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: Role
    content: str
    citations: Optional[List[Citation]] = None


class ChatRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None, description="Logical user identifier (demo or auth-derived)"
    )
    conversation_id: Optional[str] = Field(
        default=None, description="Existing conversation ID, if continuing a thread"
    )
    message: str = Field(..., description="User message content")
    stream: bool = Field(
        default=False,
        description="Whether the client prefers a streaming response",
    )


class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessage


class ChatStreamChunk(BaseModel):
    """Shape for streaming chat chunks."""

    type: str = Field(description="Chunk type, e.g., 'delta' or 'done'")
    delta: Optional[str] = Field(
        default=None, description="Token/text delta for this chunk"
    )
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None

