from __future__ import annotations

import io
import logging
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter 
from pypdf import PdfReader

from .vectorstore import add_texts


logger = logging.getLogger(__name__)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=160,
    separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
)


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    texts: List[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        if page_text:
            texts.append(page_text)
    return "\n\n".join(texts)


def _extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")


def ingest_document(
    file_bytes: bytes,
    filename: str,
    session_id: str,
) -> Dict[str, Any]:
    """Parse, chunk, and index a document."""
    if filename.lower().endswith(".pdf"):
        raw_text = _extract_text_from_pdf(file_bytes)
        doc_type = "pdf"
    else:
        raw_text = _extract_text_from_txt(file_bytes)
        doc_type = "text"

    if not raw_text.strip():
        logger.warning("Uploaded document '%s' is empty after parsing.", filename)
        return {"num_chunks": 0, "backend": "none"}

    chunks = text_splitter.split_text(raw_text)
    metadatas = [
        {
            "source": filename,
            "session_id": session_id,
            "chunk_index": idx,
            "doc_type": doc_type,
        }
        for idx, _ in enumerate(chunks)
    ]

    num_chunks, backend = add_texts(chunks, metadatas)
    logger.info(
        "Ingested document '%s' for session '%s' into %s with %d chunks",
        filename,
        session_id,
        backend,
        num_chunks,
    )
    return {"num_chunks": num_chunks, "backend": backend}

