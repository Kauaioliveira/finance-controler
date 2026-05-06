from __future__ import annotations

from datetime import datetime

from app.core.exceptions import NotFoundError
from app.repositories.database import database


class AuthSessionRepository:
    def create_session(
        self,
        *,
        session_id: str,
        user_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> None:
        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO auth_sessions (
                    id,
                    user_id,
                    refresh_token_hash,
                    expires_at
                )
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, user_id, refresh_token_hash, expires_at),
            )

    def get_session(self, session_id: str) -> dict:
        with database.connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    refresh_token_hash,
                    expires_at,
                    revoked_at,
                    last_used_at,
                    created_at,
                    updated_at
                FROM auth_sessions
                WHERE id = %s
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("Sessao de autenticacao nao encontrada.")
        return row

    def rotate_session(
        self,
        *,
        session_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> None:
        with database.connection() as connection:
            row = connection.execute(
                """
                UPDATE auth_sessions
                SET
                    refresh_token_hash = %s,
                    expires_at = %s,
                    revoked_at = NULL,
                    last_used_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (refresh_token_hash, expires_at, session_id),
            ).fetchone()
        if row is None:
            raise NotFoundError("Sessao de autenticacao nao encontrada.")

    def revoke_session(self, session_id: str) -> None:
        with database.connection() as connection:
            connection.execute(
                """
                UPDATE auth_sessions
                SET
                    revoked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (session_id,),
            )
