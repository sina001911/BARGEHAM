"""Application configuration using Pydantic Settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "BARGEHAM"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- Database ---
    db_name: str = "bargeham"
    db_user: str = "uxup"
    db_password: str = "uxup_dev"
    db_host: str = "localhost"
    db_port: int = 5433

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/0"

    # --- Storage ---
    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_secure: bool = False
    storage_bucket: str = "bargeham-documents"

    # --- Security ---
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # --- OCR ---
    ocr_engine: str = "paddleocr"  # paddleocr | tesseract
    ocr_fallback_engine: str = "tesseract"
    ocr_languages: str = "fas+eng"
    ocr_confidence_threshold: float = 0.6

    # --- AI ---
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    embedding_model: str = "sentence-transformers/paraphrase-MultiLM-MiniLM-L12-v2"
    embedding_fallback_model: str = "Msobhi/Persian_Sentence_Embedding_v3"
    embedding_dim: int = 1024
    embedding_enabled: bool = True
    max_chunks_per_query: int = 8
    max_tokens_per_answer: int = 2000
    ai_temperature: float = 0.1
    prefer_cloud_chat: bool = False

    # --- Search ---
    search_fts_limit: int = 50
    search_vector_limit: int = 50
    search_hybrid_limit: int = 30

    # --- Upload ---
    max_upload_size_mb: int = 100
    allowed_mime_types: str = (
        "application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "text/plain,"
        "image/png,image/jpeg,image/tiff,image/webp"
    )

    # --- Classification ---
    classification_enabled: bool = True
    classification_categories: str = (
        "contract,invoice,receipt,report,book,personal_document,"
        "technical_document,correspondence,other"
    )
    classification_confidence_threshold: float = 0.5

    # --- Duplicate Detection ---
    duplicate_detection_enabled: bool = True
    duplicate_similarity_threshold: float = 0.85  # MinHash Jaccard threshold

    # --- Rate limiting ---
    rate_limit_auth: int = 5
    rate_limit_search: int = 60
    rate_limit_upload: int = 20

    # --- Observability ---
    log_level: str = "INFO"
    log_format: str = "json"
    prometheus_enabled: bool = True

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()