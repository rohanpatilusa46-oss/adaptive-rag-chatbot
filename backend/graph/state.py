from __future__ import annotations

from typing import Dict, List, Literal, Optional, TypedDict, Any


RouteType = Literal["documents", "general", "web"]


class GraphState(TypedDict, total=False):
    query: str
    session_id: str
    route: RouteType
    rewritten_query: str
    documents: List[Any]
    answer: str
    debug: Dict[str, Any]
    history: List[Dict[str, str]]

