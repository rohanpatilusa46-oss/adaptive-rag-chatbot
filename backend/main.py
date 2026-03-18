from __future__ import annotations

import logging
from typing import Dict, Any
import uuid

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.logging_config import setup_logging
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    HealthResponse,
    NewSessionResponse,
)
from backend.ingestion import ingest_document
from backend.memory import append_message, get_history, mongo_available
from backend.vectorstore import get_vectorstore
from backend.graph.graph_builder import build_graph
from backend.graph.state import GraphState


setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="Adaptive RAG Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GRAPH = build_graph()


@app.post("/session", response_model=NewSessionResponse)
async def create_session() -> NewSessionResponse:
    """Create a new chat session ID. Existing sessions remain intact."""
    new_id = str(uuid.uuid4())
    logger.info("Created new session id='%s'", new_id)
    return NewSessionResponse(session_id=new_id)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    backend = "none"
    try:
        vs = get_vectorstore()
        backend = vs.backend
    except Exception:
        backend = "none"
    return HealthResponse(
        status="ok",
        vector_backend=backend,  # type: ignore[arg-type]
        mongo_connected=mongo_available(),
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> UploadResponse:
    content = await file.read()
    result = ingest_document(content, file.filename, session_id=session_id)
    return UploadResponse(
        session_id=session_id,
        num_chunks=result.get("num_chunks", 0),
        backend=result.get("backend", "none"),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    logger.info("Received chat request for session '%s'", request.session_id)

    # Combine client-provided history (if any) with server-side memory.
    history_from_client = [
        {"role": m.role, "content": m.content} for m in (request.messages or [])
    ]
    history_from_db = get_history(request.session_id, limit=request.history_limit)
    history = history_from_client or history_from_db

    state: GraphState = {
        "query": request.message,
        "session_id": request.session_id,
        "history": history,
        "debug": {},
    }

    try:
        result: Dict[str, Any] = GRAPH.invoke(state)
    except Exception as exc:
        logger.exception("Error while processing graph: %s", exc)
        return ChatResponse(
            session_id=request.session_id,
            answer="Sorry, an internal error occurred while processing your request.",
            route="general",
            used_docs=[],
            debug_info={"error": str(exc)},
        )

    answer = result.get("answer", "")
    route = result.get("route", "general")
    docs = result.get("documents") or []
    debug = result.get("debug") or {}

    # Persist conversation if Mongo is available
    append_message(request.session_id, "user", request.message)
    append_message(request.session_id, "assistant", answer)

    # Serialize used docs minimally
    used_docs = []
    for d in docs:
        used_docs.append(
            {
                "content": d.page_content,
                "metadata": d.metadata,
            }
        )

    logger.info(
        "Completed chat request for session '%s' via route '%s' with %d used docs.",
        request.session_id,
        route,
        len(used_docs),
    )

    return ChatResponse(
        session_id=request.session_id,
        answer=answer,
        route=route,  # type: ignore[arg-type]
        used_docs=used_docs,
        debug_info=debug,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

