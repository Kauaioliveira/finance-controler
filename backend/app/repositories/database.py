from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.core.config import get_settings
from app.core.exceptions import InfrastructureError
from app.core.security import hash_password


class PostgresDatabase:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.schema_ready = False
        self.last_error: str | None = None

    def initialize(self) -> None:
        settings = get_settings()
        dimensions = int(settings.openai_embeddings_dimensions)

        statements = [
            "CREATE EXTENSION IF NOT EXISTS vector",
            """
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_login_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                refresh_token_hash TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ,
                last_used_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
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
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector({dimensions}) NOT NULL,
                metadata_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
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
            """
            CREATE TABLE IF NOT EXISTS finance_imports (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                uploaded_by_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                filename TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'csv',
                status TEXT NOT NULL,
                currency TEXT NOT NULL DEFAULT 'BRL',
                total_rows INTEGER NOT NULL DEFAULT 0,
                processed_rows INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finalized_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS finance_transactions (
                id TEXT PRIMARY KEY,
                import_id TEXT NOT NULL REFERENCES finance_imports(id) ON DELETE CASCADE,
                row_number INTEGER NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount NUMERIC(14, 2) NOT NULL,
                direction TEXT NOT NULL,
                predicted_category TEXT NOT NULL,
                final_category TEXT NOT NULL,
                category_confidence DOUBLE PRECISION NOT NULL,
                review_notes TEXT,
                reviewed_by_user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                reviewed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS finance_report_snapshots (
                id TEXT PRIMARY KEY,
                import_id TEXT NOT NULL REFERENCES finance_imports(id) ON DELETE CASCADE,
                summary_json JSONB NOT NULL,
                categories_json JSONB NOT NULL,
                monthly_json JSONB NOT NULL,
                top_transactions_json JSONB NOT NULL,
                insights_json JSONB NOT NULL,
                narrative TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)",
            (
                "CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding "
                "ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            ),
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_finance_imports_company_id ON finance_imports(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_finance_imports_status ON finance_imports(status)",
            "CREATE INDEX IF NOT EXISTS idx_finance_imports_uploaded_by_user_id ON finance_imports(uploaded_by_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_finance_transactions_import_id ON finance_transactions(import_id)",
            "CREATE INDEX IF NOT EXISTS idx_finance_transactions_final_category ON finance_transactions(final_category)",
            "CREATE INDEX IF NOT EXISTS idx_finance_report_snapshots_import_id ON finance_report_snapshots(import_id)",
        ]

        try:
            with self._open_connection(register_vector_type=False) as connection:
                for statement in statements:
                    connection.execute(statement)
                register_vector(connection)
                self._ensure_seed_data(connection)
            self.schema_ready = True
            self.last_error = None
        except InfrastructureError as exc:
            self.schema_ready = False
            self.last_error = exc.detail

    def _ensure_seed_data(self, connection) -> None:
        settings = get_settings()
        company = connection.execute(
            "SELECT id, name FROM companies ORDER BY created_at ASC LIMIT 1"
        ).fetchone()

        if company is None:
            company_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO companies (id, name)
                VALUES (%s, %s)
                """,
                (company_id, settings.seed_company_name),
            )
        else:
            company_id = company["id"]

        admin = connection.execute(
            "SELECT id FROM users WHERE email = %s",
            (settings.seed_admin_email.lower(),),
        ).fetchone()
        if admin is None:
            connection.execute(
                """
                INSERT INTO users (
                    id,
                    company_id,
                    name,
                    email,
                    password_hash,
                    role,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, 'admin', TRUE)
                """,
                (
                    str(uuid4()),
                    company_id,
                    settings.seed_admin_name,
                    settings.seed_admin_email.lower(),
                    hash_password(settings.seed_admin_password),
                ),
            )

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
