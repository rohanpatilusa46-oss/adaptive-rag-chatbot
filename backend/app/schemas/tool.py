from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
  name: str
  type: str
  description: str
  required: bool = True


class ToolDefinition(BaseModel):
  name: str
  description: str
  parameters: List[ToolParameter] = Field(
      default_factory=list, description="Flat parameter schema for the tool"
  )


class SearchResult(BaseModel):
  title: str
  url: str
  snippet: str
  content: Optional[str] = None


class SearchToolInput(BaseModel):
  query: str
  max_results: int = 5


class SearchToolOutput(BaseModel):
  query: str
  results: List[SearchResult]


class SaveMemoryInput(BaseModel):
  user_id: str
  key: str
  value: str
  category: str = "preference"


class SaveMemoryOutput(BaseModel):
  success: bool
  memory_id: Optional[str] = None


class GetMemoryInput(BaseModel):
  user_id: str


class MemoryEntrySchema(BaseModel):
  id: str
  key: str
  value: str
  category: str


class GetMemoryOutput(BaseModel):
  entries: List[MemoryEntrySchema]

