from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS, Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from .config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


STORAGE_DIR = Path(os.getenv("VECTORSTORE_DIR", Path(__file__).resolve().parent.parent / "storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
FAISS_INDEX_PATH = STORAGE_DIR / "faiss_index.pkl"


@dataclass
class VectorStoreWrapper:
    backend: str
    store: Any


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model_name, api_key=settings.openai_api_key)


def init_qdrant() -> Optional[VectorStoreWrapper]:
    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=5.0,
        )
        # Ensure collection exists (lazy creation)
        embeddings = _get_embeddings()
        vector_size = 1536

        existing = client.get_collections()
        if not any(c.name == settings.qdrant_collection for c in existing.collections):
            logger.info("Creating Qdrant collection '%s'", settings.qdrant_collection)
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
            )

        vs = Qdrant(
            client=client,
            collection_name=settings.qdrant_collection,
            embeddings=embeddings,
        )
        logger.info("Using Qdrant vector store at %s", settings.qdrant_url)
        return VectorStoreWrapper(backend="qdrant", store=vs)
    except Exception as exc:
        logger.warning("Failed to initialize Qdrant, will try FAISS fallback: %s", exc)
        return None


def init_faiss() -> VectorStoreWrapper:
    embeddings = _get_embeddings()

    if FAISS_INDEX_PATH.exists():
        try:
            with FAISS_INDEX_PATH.open("rb") as f:
                store = pickle.load(f)
            logger.info("Loaded existing FAISS index from %s", FAISS_INDEX_PATH)
            return VectorStoreWrapper(backend="faiss", store=store)
        except Exception as exc:
            logger.warning("Failed to load existing FAISS index, creating a new one: %s", exc)

    # ✅ Create FAISS with ONE dummy entry
    store = FAISS.from_texts(
        texts=["initial dummy text"],
        embedding=embeddings,
        metadatas=[{"dummy": True}]
    )

    logger.info("Initialized new FAISS index in memory")
    return VectorStoreWrapper(backend="faiss", store=store)


_VECTORSTORE: Optional[VectorStoreWrapper] = None


def get_vectorstore() -> VectorStoreWrapper:
    global _VECTORSTORE
    if _VECTORSTORE is not None:
        return _VECTORSTORE

    vs = init_qdrant()
    if vs is None:
        vs = init_faiss()
    _VECTORSTORE = vs
    return vs


def persist_faiss_if_needed() -> None:
    if _VECTORSTORE is None or _VECTORSTORE.backend != "faiss":
        return
    try:
        with FAISS_INDEX_PATH.open("wb") as f:
            pickle.dump(_VECTORSTORE.store, f)
        logger.info("Persisted FAISS index to %s", FAISS_INDEX_PATH)
    except Exception as exc:
        logger.warning("Failed to persist FAISS index: %s", exc)


def add_texts(
    texts: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[int, str]:
    """Add texts to the current vector store. Returns (num_chunks, backend)."""
    vs = get_vectorstore()
    logger.info("Adding %d texts to vector store (%s)", len(texts), vs.backend)
    vs.store.add_texts(texts=texts, metadatas=metadatas or [{} for _ in texts])

    if vs.backend == "faiss":
        persist_faiss_if_needed()

    return len(texts), vs.backend


def similarity_search(
    query: str,
    k: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None,
):
    vs = get_vectorstore()
    if metadata_filter:
        return vs.store.similarity_search(query, k=k, filter=metadata_filter)
    return vs.store.similarity_search(query, k=k)


def similarity_search_with_score(
    query: str,
    k: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None,
):
    """
    Wrapper around LangChain's similarity_search_with_score.
    Returns a list of (Document, score) where higher scores mean more similar.
    """
    vs = get_vectorstore()
    if hasattr(vs.store, "similarity_search_with_score"):
        if metadata_filter:
            return vs.store.similarity_search_with_score(query, k=k, filter=metadata_filter)
        return vs.store.similarity_search_with_score(query, k=k)
    # Fallback if backend doesn't support scores: return docs with a dummy score.
    docs = similarity_search(query, k=k, metadata_filter=metadata_filter)
    return [(d, 0.0) for d in docs]

