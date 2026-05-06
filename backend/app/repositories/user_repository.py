from __future__ import annotations

from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.database import database


class UserRepository:
    def get_user_by_email(self, email: str) -> dict | None:
        with database.connection() as connection:
            return connection.execute(
                """
                SELECT
                    u.id,
                    u.company_id,
                    u.name,
                    u.email,
                    u.password_hash,
                    u.role,
                    u.is_active,
                    u.created_at,
                    u.updated_at,
                    u.last_login_at,
                    c.name AS company_name
                FROM users AS u
                INNER JOIN companies AS c ON c.id = u.company_id
                WHERE LOWER(u.email) = LOWER(%s)
                """,
                (email,),
            ).fetchone()

    def get_user_by_id(self, user_id: str) -> dict:
        with database.connection() as connection:
            row = connection.execute(
                """
                SELECT
                    u.id,
                    u.company_id,
                    u.name,
                    u.email,
                    u.password_hash,
                    u.role,
                    u.is_active,
                    u.created_at,
                    u.updated_at,
                    u.last_login_at,
                    c.name AS company_name
                FROM users AS u
                INNER JOIN companies AS c ON c.id = u.company_id
                WHERE u.id = %s
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("Usuario nao encontrado.")
        return row

    def list_users(self, company_id: str, *, limit: int, offset: int) -> list[dict]:
        with database.connection() as connection:
            return connection.execute(
                """
                SELECT
                    u.id,
                    u.company_id,
                    u.name,
                    u.email,
                    u.role,
                    u.is_active,
                    u.created_at,
                    u.updated_at,
                    c.name AS company_name
                FROM users AS u
                INNER JOIN companies AS c ON c.id = u.company_id
                WHERE u.company_id = %s
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (company_id, limit, offset),
            ).fetchall()

    def count_users(self, company_id: str) -> int:
        with database.connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM users WHERE company_id = %s",
                (company_id,),
            ).fetchone()
        return int(row["total"])

    def create_user(
        self,
        *,
        company_id: str,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> dict:
        existing = self.get_user_by_email(email)
        if existing is not None:
            raise ConflictError("Ja existe um usuario com este email.")

        user_id = str(uuid4())
        with database.connection() as connection:
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
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                """,
                (user_id, company_id, name, email.lower(), password_hash, role),
            )
        return self.get_user_by_id(user_id)

    def update_user(
        self,
        *,
        user_id: str,
        company_id: str,
        name: str | None = None,
        role: str | None = None,
    ) -> dict:
        current = self.get_user_by_id(user_id)
        if current["company_id"] != company_id:
            raise NotFoundError("Usuario nao encontrado.")

        with database.connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET
                    name = COALESCE(%s, name),
                    role = COALESCE(%s, role),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (name, role, user_id),
            )
        return self.get_user_by_id(user_id)

    def update_password(
        self,
        *,
        user_id: str,
        company_id: str,
        password_hash: str,
    ) -> None:
        current = self.get_user_by_id(user_id)
        if current["company_id"] != company_id:
            raise NotFoundError("Usuario nao encontrado.")

        with database.connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET
                    password_hash = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (password_hash, user_id),
            )

    def set_user_status(
        self,
        *,
        user_id: str,
        company_id: str,
        is_active: bool,
    ) -> dict:
        current = self.get_user_by_id(user_id)
        if current["company_id"] != company_id:
            raise NotFoundError("Usuario nao encontrado.")

        with database.connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET
                    is_active = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (is_active, user_id),
            )
        return self.get_user_by_id(user_id)

    def touch_last_login(self, user_id: str) -> None:
        with database.connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET
                    last_login_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (user_id,),
            )
