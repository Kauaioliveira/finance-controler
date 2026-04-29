from __future__ import annotations

from psycopg.types.json import Jsonb

from app.repositories.database import database


class ChatRepository:
    def initialize(self) -> None:
        database.initialize()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: list[dict[str, object]] | None = None,
        confidence_hint: str | None = None,
    ) -> None:
        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO chat_sessions (session_id, updated_at)
                VALUES (%s, NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET updated_at = EXCLUDED.updated_at
                """,
                (session_id,),
            )
            connection.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, sources, confidence_hint)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    role,
                    content,
                    Jsonb(sources or []),
                    confidence_hint,
                ),
            )

    def get_session_messages(self, session_id: str, limit: int) -> list[dict]:
        with database.connection() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at, sources, confidence_hint
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (session_id, limit),
            ).fetchall()

        return list(reversed(rows))
