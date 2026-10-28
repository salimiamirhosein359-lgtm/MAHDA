"""AI Sentinel — application configuration (pydantic-settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    db_backend: str = "postgres"  # "postgres" | "sqlite" (development fallback)
    sqlite_path: str = "ai_sentinel.db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ai_sentinel"
    postgres_password: str = "change_me"
    postgres_db: str = "ai_sentinel"

    # --- LLM ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "gpt-4o-mini"
    llm_model_fallback: str = "ollama/qwen2.5"

    # --- Embeddings ---
    embedding_provider: str = "local"  # "local" | "openai"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    openai_embedding_model: str = "text-embedding-3-small"

    # --- Web search ---
    web_search_provider: str = "searxng"  # "searxng" | "tavily" | "brave"
    searxng_url: str = "http://localhost:8080"
    tavily_api_key: str = ""
    brave_api_key: str = ""

    # --- Whisper ---
    whisper_provider: str = "local"
    whisper_model: str = "small"

    # --- Collectors ---
    collect_interval_minutes: int = 60

    # --- App ---
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.db_backend.lower() == "sqlite"

    @property
    def database_url(self) -> str:
        if self.is_sqlite:
            return f"sqlite:///{self.sqlite_path}"
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_async(self) -> str:
        return self.database_url.replace("+psycopg2", "+asyncpg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
