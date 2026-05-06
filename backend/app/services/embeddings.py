from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.exceptions import InfrastructureError


class EmbeddingService:
    def __init__(self) -> None:
        self._client: OpenAIEmbeddings | None = None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._get_client().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._get_client().embed_query(text)

    def _get_client(self) -> OpenAIEmbeddings:
        settings = get_settings()
        if settings.demo_mode:
            raise InfrastructureError(
                "OPENAI_API_KEY nao configurada. A indexacao e a busca vetorial precisam de uma chave valida."
            )
        if self._client is None:
            self._client = OpenAIEmbeddings(
                model=settings.openai_embeddings_model,
                api_key=settings.openai_api_key,
                dimensions=settings.openai_embeddings_dimensions,
            )
        return self._client


embedding_service = EmbeddingService()
