# Student AI Platform — Lightweight Local Runner
# Uses SQLite instead of PostgreSQL, no Redis, no external services needed.

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Student AI Platform"
    app_version: str = "1.0.0"
    debug: bool = True

    # SQLite for local dev (no PostgreSQL needed)
    database_url: str = "sqlite+aiosqlite:///./student_ai_local.db"
    database_url_sync: str = "sqlite:///./student_ai_local.db"

    # Disable Redis (use in-memory fallback)
    redis_url: str = "redis://localhost:6379/0"
    use_redis: bool = False

    # LLM keys (optional — agents work in demo mode without them)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ibm_api_key: str = ""
    ibm_project_id: str = ""
    ibm_url: str = "https://us-south.ml.cloud.ibm.com"

    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "student-ai-platform"

    secret_key: str = "local-dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    chroma_persist_dir: str = "./chroma_data_local"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_resumes: str = "resumes"
    minio_secure: bool = False

    daily_token_budget_usd: float = 5.0
    allowed_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000", "null"]

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
