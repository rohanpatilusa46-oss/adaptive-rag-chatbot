import os
from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv


# 👇 FORCE correct path to root .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

print("DEBUG ENV PATH:", ENV_PATH)
print("DEBUG OPENAI KEY:", os.getenv("OPENAI_API_KEY"))

class Settings(BaseModel):
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    tavily_api_key: str = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))

    qdrant_url: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant_api_key: str = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))
    qdrant_collection: str = Field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "documents"))

    mongodb_uri: str = Field(default_factory=lambda: os.getenv("MONGODB_URI", ""))
    mongodb_db_name: str = Field(default_factory=lambda: os.getenv("MONGODB_DB_NAME", "adaptive_rag"))
    mongodb_collection_name: str = Field(default_factory=lambda: os.getenv("MONGODB_COLLECTION_NAME", "conversations"))

    model_name: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini"))
    embedding_model_name: str = Field(default_factory=lambda: os.getenv("OPENAI_EMBEDDING_MODEL_NAME", "text-embedding-3-small"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

