from __future__ import annotations

from psycopg.types.json import Jsonb

from app.core.exceptions import NotFoundError
from app.repositories.database import database


class ChatRepository:
    def initialize(self) -> None:
        database.initialize()

    def save_turn(
        self,
        session_id: str,
        owner_user_id: str,
        company_id: str,
        user_message: str,
        answer: str,
        sources: list[dict[str, object]] | None = None,
        confidence_hint: str | None = None,
    ) -> None:
        with database.connection() as connection:
            self._ensure_session_access(
                connection,
                session_id=session_id,
                owner_user_id=owner_user_id,
                company_id=company_id,
            )
            connection.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, sources, confidence_hint)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    "human",
                    user_message,
                    Jsonb([]),
                    None,
                ),
            )
            connection.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, sources, confidence_hint)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    "ai",
                    answer,
                    Jsonb(sources or []),
                    confidence_hint,
                ),
            )

    def get_session_messages(
        self,
        *,
        session_id: str,
        owner_user_id: str,
        company_id: str,
        limit: int,
    ) -> list[dict]:
        with database.connection() as connection:
            self._require_session_access(
                connection,
                session_id=session_id,
                owner_user_id=owner_user_id,
                company_id=company_id,
            )
            rows = connection.execute(
                """
                SELECT m.role, m.content, m.created_at, m.sources, m.confidence_hint
                FROM chat_messages AS m
                INNER JOIN chat_sessions AS s ON s.session_id = m.session_id
                WHERE m.session_id = %s
                  AND s.owner_user_id = %s
                  AND s.company_id = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (session_id, owner_user_id, company_id, limit),
            ).fetchall()

        return list(reversed(rows))

    def _ensure_session_access(
        self,
        connection,
        *,
        session_id: str,
        owner_user_id: str,
        company_id: str,
    ) -> None:
        session = connection.execute(
            """
            SELECT session_id, owner_user_id, company_id
            FROM chat_sessions
            WHERE session_id = %s
            """,
            (session_id,),
        ).fetchone()

        if session is None:
            connection.execute(
                """
                INSERT INTO chat_sessions (session_id, owner_user_id, company_id, updated_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (session_id, owner_user_id, company_id),
            )
            return

        if (
            session.get("owner_user_id") != owner_user_id
            or session.get("company_id") != company_id
        ):
            raise NotFoundError("Sessao de chat nao encontrada.")

        connection.execute(
            """
            UPDATE chat_sessions
            SET updated_at = NOW()
            WHERE session_id = %s
            """,
            (session_id,),
        )

    def _require_session_access(
        self,
        connection,
        *,
        session_id: str,
        owner_user_id: str,
        company_id: str,
    ) -> None:
        session = connection.execute(
            """
            SELECT session_id
            FROM chat_sessions
            WHERE session_id = %s
              AND owner_user_id = %s
              AND company_id = %s
            """,
            (session_id, owner_user_id, company_id),
        ).fetchone()
        if session is None:
            raise NotFoundError("Sessao de chat nao encontrada.")
