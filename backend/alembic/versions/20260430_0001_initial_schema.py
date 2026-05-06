"""initial schema

Revision ID: 20260430_0001
Revises:
Create Date: 2026-04-30 00:00:00
"""

from __future__ import annotations

from alembic import op


revision = "20260430_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
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
        (
            "CREATE INDEX IF NOT EXISTS idx_finance_imports_uploaded_by_user_id "
            "ON finance_imports(uploaded_by_user_id)"
        ),
        "CREATE INDEX IF NOT EXISTS idx_finance_transactions_import_id ON finance_transactions(import_id)",
        (
            "CREATE INDEX IF NOT EXISTS idx_finance_transactions_final_category "
            "ON finance_transactions(final_category)"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_finance_report_snapshots_import_id "
            "ON finance_report_snapshots(import_id)"
        ),
    ]

    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    statements = [
        "DROP TABLE IF EXISTS finance_report_snapshots",
        "DROP TABLE IF EXISTS finance_transactions",
        "DROP TABLE IF EXISTS finance_imports",
        "DROP TABLE IF EXISTS chat_messages",
        "DROP TABLE IF EXISTS chat_sessions",
        "DROP TABLE IF EXISTS document_chunks",
        "DROP TABLE IF EXISTS documents",
        "DROP TABLE IF EXISTS auth_sessions",
        "DROP TABLE IF EXISTS users",
        "DROP TABLE IF EXISTS companies",
    ]

    for statement in statements:
        op.execute(statement)
