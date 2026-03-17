from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tool import (
    GetMemoryInput,
    GetMemoryOutput,
    SaveMemoryInput,
    SaveMemoryOutput,
    SearchToolInput,
    SearchToolOutput,
    ToolDefinition,
    ToolParameter,
)
from app.tools.memory_tool import GetMemoryTool, SaveMemoryTool
from app.tools.search_tool import SearchTool

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=List[ToolDefinition], summary="List supported tools")
async def list_tools() -> List[ToolDefinition]:
    """List tools available to the agent."""
    return [
        ToolDefinition(
            name="search_web",
            description="Searches the web for up-to-date information and relevant sources.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search query describing what to look up.",
                    required=True,
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of search results to return.",
                    required=False,
                ),
            ],
        ),
        ToolDefinition(
            name="save_memory",
            description="Stores a user-specific fact or preference in long-term memory.",
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="Identifier of the user the memory belongs to.",
                    required=True,
                ),
                ToolParameter(
                    name="key",
                    type="string",
                    description="Short key describing the memory (e.g. 'preferred_job_location').",
                    required=True,
                ),
                ToolParameter(
                    name="value",
                    type="string",
                    description="The value or fact to remember.",
                    required=True,
                ),
                ToolParameter(
                    name="category",
                    type="string",
                    description="Category of memory, such as 'preference' or 'fact'.",
                    required=False,
                ),
            ],
        ),
        ToolDefinition(
            name="get_memory",
            description="Retrieves long-term memory entries for a given user.",
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="Identifier of the user whose memory to fetch.",
                    required=True,
                )
            ],
        ),
    ]


@router.post(
    "/search",
    response_model=SearchToolOutput,
    summary="Execute web search tool directly",
)
async def execute_search_tool(
    payload: SearchToolInput,
    db: AsyncSession = Depends(get_db),
) -> SearchToolOutput:
    tool = SearchTool(db=db)
    output, _ = await tool.run(payload.model_dump())
    return output


@router.post(
    "/memory/save",
    response_model=SaveMemoryOutput,
    summary="Execute save_memory tool directly",
)
async def execute_save_memory_tool(
    payload: SaveMemoryInput,
    db: AsyncSession = Depends(get_db),
) -> SaveMemoryOutput:
    tool = SaveMemoryTool(db=db)
    output, _ = await tool.run(payload.model_dump())
    return output


@router.post(
    "/memory/get",
    response_model=GetMemoryOutput,
    summary="Execute get_memory tool directly",
)
async def execute_get_memory_tool(
    payload: GetMemoryInput,
    db: AsyncSession = Depends(get_db),
) -> GetMemoryOutput:
    tool = GetMemoryTool(db=db)
    output, _ = await tool.run(payload.model_dump())
    return output

