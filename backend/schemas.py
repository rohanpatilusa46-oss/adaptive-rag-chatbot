from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated session identifier")
    message: str
    history_limit: int = Field(50, description="Number of past messages to include from memory")
    messages: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional recent conversation history from the client (most recent last).",
    )


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    route: Literal["documents", "general", "web"]
    used_docs: List[Dict[str, Any]] = Field(default_factory=list)
    debug_info: Dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    session_id: str
    num_chunks: int
    backend: Literal["qdrant", "faiss"]


class HealthResponse(BaseModel):
    status: str
    vector_backend: Literal["qdrant", "faiss", "none"]
    mongo_connected: bool

