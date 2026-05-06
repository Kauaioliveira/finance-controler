from __future__ import annotations

from uuid import uuid4

from pgvector.psycopg import Vector
from psycopg.types.json import Jsonb

from app.core.exceptions import NotFoundError
from app.repositories.database import database


class DocumentRepository:
    def create_document_with_chunks(
        self,
        *,
        filename: str,
        content_type: str,
        extracted_text: str,
        chunks: list[dict[str, object]],
    ) -> dict:
        document_id = str(uuid4())
        word_count = len(extracted_text.split())

        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id,
                    filename,
                    content_type,
                    source_type,
                    status,
                    extracted_text,
                    chunk_count,
                    word_count
                )
                VALUES (%s, %s, %s, 'upload', 'approved', %s, %s, %s)
                """,
                (
                    document_id,
                    filename,
                    content_type,
                    extracted_text,
                    len(chunks),
                    word_count,
                ),
            )

            for chunk in chunks:
                connection.execute(
                    """
                    INSERT INTO document_chunks (
                        id,
                        document_id,
                        chunk_index,
                        content,
                        embedding,
                        metadata_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        document_id,
                        chunk["chunk_index"],
                        chunk["content"],
                        Vector(chunk["embedding"]),
                        Jsonb(chunk["metadata_json"]),
                    ),
                )

        return self.get_document(document_id)

    def list_documents(self) -> list[dict]:
        with database.connection() as connection:
            return connection.execute(
                """
                SELECT
                    id,
                    filename,
                    content_type,
                    source_type,
                    status,
                    chunk_count,
                    word_count,
                    created_at,
                    updated_at
                FROM documents
                ORDER BY updated_at DESC, created_at DESC
                """
            ).fetchall()

    def get_document(self, document_id: str) -> dict:
        with database.connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    filename,
                    content_type,
                    source_type,
                    status,
                    chunk_count,
                    word_count,
                    created_at,
                    updated_at,
                    LEFT(extracted_text, 500) AS preview
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            ).fetchone()

        if row is None:
            raise NotFoundError("Documento nao encontrado.")

        return row

    def get_document_text(self, document_id: str) -> dict:
        with database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, filename, content_type, extracted_text
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            ).fetchone()

        if row is None:
            raise NotFoundError("Documento nao encontrado.")

        return row

    def delete_document(self, document_id: str) -> None:
        with database.connection() as connection:
            row = connection.execute(
                "DELETE FROM documents WHERE id = %s RETURNING id",
                (document_id,),
            ).fetchone()

        if row is None:
            raise NotFoundError("Documento nao encontrado.")

    def replace_document_chunks(
        self,
        document_id: str,
        *,
        content_type: str,
        extracted_text: str,
        chunks: list[dict[str, object]],
    ) -> dict:
        word_count = len(extracted_text.split())

        with database.connection() as connection:
            existing = connection.execute(
                "SELECT id, filename FROM documents WHERE id = %s",
                (document_id,),
            ).fetchone()
            if existing is None:
                raise NotFoundError("Documento nao encontrado.")

            connection.execute(
                """
                UPDATE documents
                SET
                    content_type = %s,
                    extracted_text = %s,
                    chunk_count = %s,
                    word_count = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    content_type,
                    extracted_text,
                    len(chunks),
                    word_count,
                    document_id,
                ),
            )
            connection.execute(
                "DELETE FROM document_chunks WHERE document_id = %s",
                (document_id,),
            )

            for chunk in chunks:
                connection.execute(
                    """
                    INSERT INTO document_chunks (
                        id,
                        document_id,
                        chunk_index,
                        content,
                        embedding,
                        metadata_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        document_id,
                        chunk["chunk_index"],
                        chunk["content"],
                        Vector(chunk["embedding"]),
                        Jsonb(chunk["metadata_json"]),
                    ),
                )

        return self.get_document(document_id)

    def search_similar_chunks(
        self,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[dict]:
        vector_query = Vector(query_embedding)
        with database.connection() as connection:
            return connection.execute(
                """
                SELECT
                    c.document_id,
                    d.filename,
                    c.chunk_index,
                    c.content,
                    c.metadata_json,
                    c.embedding <=> %s AS distance
                FROM document_chunks AS c
                INNER JOIN documents AS d ON d.id = c.document_id
                WHERE d.status = 'approved'
                ORDER BY c.embedding <=> %s
                LIMIT %s
                """,
                (vector_query, vector_query, limit),
            ).fetchall()
