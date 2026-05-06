from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.config import get_settings
from app.repositories.document_repository import DocumentRepository
from app.services.embeddings import embedding_service


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    chunk_index: int
    content: str
    distance: float


@dataclass
class RetrievedSource:
    filename: str
    source_label: str
    document_id: str
    chunk_index: int
    excerpt: str
    score: float


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    sources: list[RetrievedSource]
    confidence_hint: Literal["low", "medium", "high"]


class RetrievalService:
    def __init__(self) -> None:
        self.repository = DocumentRepository()

    def search(self, query: str) -> RetrievalResult:
        settings = get_settings()
        query_embedding = embedding_service.embed_query(query)
        rows = self.repository.search_similar_chunks(
            query_embedding,
            limit=settings.rag_top_k,
        )

        relevant_chunks = [
            RetrievedChunk(
                document_id=row["document_id"],
                filename=row["filename"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                distance=float(row["distance"]),
            )
            for row in rows
            if float(row["distance"]) <= settings.rag_max_distance
        ]

        confidence_hint = self._build_confidence_hint(len(relevant_chunks))
        sources = [
            RetrievedSource(
                filename=chunk.filename,
                source_label=f"{chunk.filename}#chunk-{chunk.chunk_index}",
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                excerpt=self._build_excerpt(chunk.content),
                score=self._build_score(chunk.distance),
            )
            for chunk in relevant_chunks
        ]

        return RetrievalResult(
            chunks=relevant_chunks,
            sources=sources,
            confidence_hint=confidence_hint,
        )

    def _build_confidence_hint(
        self,
        relevant_count: int,
    ) -> Literal["low", "medium", "high"]:
        if relevant_count >= 3:
            return "high"
        if relevant_count >= 1:
            return "medium"
        return "low"

    def _build_excerpt(self, content: str) -> str:
        settings = get_settings()
        excerpt = " ".join(content.split())
        limit = settings.source_excerpt_length
        if len(excerpt) <= limit:
            return excerpt
        return f"{excerpt[: limit - 3].rstrip()}..."

    def _build_score(self, distance: float) -> float:
        score = max(0.0, min(1.0, 1.0 - distance))
        return round(score, 4)


retrieval_service = RetrievalService()
