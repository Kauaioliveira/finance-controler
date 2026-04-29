from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Assistente Contabil API"
    app_env: str = "development"
    app_debug: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embeddings_model: str = "text-embedding-3-small"
    openai_embeddings_dimensions: int = 1536
    max_chat_history: int = 6
    database_url: str = "postgresql://postgres:postgres@localhost:5432/assistente_contabil"
    database_connect_timeout: int = 3
    rag_top_k: int = 4
    rag_max_distance: float = 0.8
    document_chunk_size: int = 1000
    document_chunk_overlap: int = 150
    source_excerpt_length: int = 220
    max_upload_size_mb: int = 10
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def demo_mode(self) -> bool:
        api_key = self.openai_api_key.strip()
        return not api_key or api_key == "coloque_sua_chave_aqui"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
