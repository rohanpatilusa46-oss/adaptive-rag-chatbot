from __future__ import annotations

import logging
from typing import List, Dict, Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


_MONGO_CLIENT: MongoClient | None = None


def _get_client() -> MongoClient | None:
    global _MONGO_CLIENT
    if _MONGO_CLIENT is not None:
        return _MONGO_CLIENT
    if not settings.mongodb_uri:
        logger.warning("MONGODB_URI not set; conversation memory will be disabled.")
        return None
    try:
        _MONGO_CLIENT = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
        # Trigger server selection
        _MONGO_CLIENT.admin.command("ping")
        logger.info("Connected to MongoDB for conversation memory.")
        return _MONGO_CLIENT
    except PyMongoError as exc:
        logger.warning("Failed to connect to MongoDB; memory disabled: %s", exc)
        _MONGO_CLIENT = None
        return None


def mongo_available() -> bool:
    return _get_client() is not None


def append_message(session_id: str, role: str, content: str) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        collection = client[settings.mongodb_db_name][settings.mongodb_collection_name]
        doc = {
            "session_id": session_id,
            "role": role,
            "content": content,
        }
        collection.insert_one(doc)
    except PyMongoError as exc:
        logger.warning("Failed to append message to MongoDB: %s", exc)


def get_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    client = _get_client()
    if client is None:
        return []
    try:
        collection = client[settings.mongodb_db_name][settings.mongodb_collection_name]
        cursor = (
            collection.find({"session_id": session_id})
            .sort("_id", -1)
            .limit(limit)
        )
        results = list(cursor)
        results.reverse()
        return [{"role": r["role"], "content": r["content"]} for r in results]
    except PyMongoError as exc:
        logger.warning("Failed to fetch history from MongoDB: %s", exc)
        return []

