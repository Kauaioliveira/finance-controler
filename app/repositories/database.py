from __future__ import annotations

from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.core.config import get_settings
from app.core.exceptions import InfrastructureError


class PostgresDatabase:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.schema_ready = False
        self.last_error: str | None = None

    def initialize(self) -> None:
        settings = get_settings()
        dimensions = int(settings.openai_embeddings_dimensions)

        create_chunks_table = f"""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector({dimensions}) NOT NULL,
            metadata_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """

        statements = [
            "CREATE EXTENSION IF NOT EXISTS vector",
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'upload',
                status TEXT NOT NULL DEFAULT 'approved',
                extracted_text TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                word_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            create_chunks_table,
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources JSONB NOT NULL DEFAULT '[]'::jsonb,
                confidence_hint TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)",
            (
                "CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding "
                "ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            ),
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)",
        ]

        try:
            with self._open_connection(register_vector_type=False) as connection:
                for statement in statements:
                    connection.execute(statement)
                register_vector(connection)
            self.schema_ready = True
            self.last_error = None
        except InfrastructureError as exc:
            self.schema_ready = False
            self.last_error = exc.detail

    def get_status(self) -> dict[str, str | bool]:
        status = "ok" if self.ping() else "degraded"
        detail = self.last_error or "PostgreSQL pronto."
        return {
            "status": status,
            "schema_ready": self.schema_ready,
            "detail": detail,
        }

    def ping(self) -> bool:
        try:
            with self._open_connection(register_vector_type=False) as connection:
                connection.execute("SELECT 1")
            self.last_error = None
            return True
        except InfrastructureError as exc:
            self.last_error = exc.detail
            return False

    @contextmanager
    def connection(self):
        if not self.schema_ready:
            self.initialize()
        with self._open_connection(register_vector_type=True) as connection:
            yield connection

    @contextmanager
    def _open_connection(self, register_vector_type: bool):
        try:
            connection = psycopg.connect(
                self.settings.database_url,
                connect_timeout=self.settings.database_connect_timeout,
                row_factory=dict_row,
            )
            if register_vector_type:
                register_vector(connection)
            yield connection
            connection.commit()
        except psycopg.Error as exc:
            message = str(exc).splitlines()[0] or exc.__class__.__name__
            self.last_error = (
                "Banco PostgreSQL indisponivel ou sem a extensao pgvector. "
                f"Detalhe: {message}"
            )
            raise InfrastructureError(self.last_error) from exc
        finally:
            if "connection" in locals():
                connection.close()


database = PostgresDatabase()
