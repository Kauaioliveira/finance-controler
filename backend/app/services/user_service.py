from __future__ import annotations

from app.core.exceptions import AuthorizationError
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    CreateUserRequest,
    UpdatePasswordRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserResponse,
)
from app.schemas.auth import CompanySummary


class UserService:
    def __init__(self) -> None:
        self.repository = UserRepository()

    def list_users(self, current_user: dict, *, page: int, page_size: int) -> UserListResponse:
        self._ensure_admin(current_user)
        offset = (page - 1) * page_size
        rows = self.repository.list_users(
            current_user["company_id"],
            limit=page_size,
            offset=offset,
        )
        total = self.repository.count_users(current_user["company_id"])
        return UserListResponse(
            items=[self._build_user_response(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def create_user(self, current_user: dict, payload: CreateUserRequest) -> UserResponse:
        self._ensure_admin(current_user)
        row = self.repository.create_user(
            company_id=current_user["company_id"],
            name=payload.name.strip(),
            email=payload.email.strip().lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        return self._build_user_response(row)

    def update_user(
        self,
        current_user: dict,
        user_id: str,
        payload: UpdateUserRequest,
    ) -> UserResponse:
        self._ensure_admin(current_user)
        row = self.repository.update_user(
            user_id=user_id,
            company_id=current_user["company_id"],
            name=payload.name.strip() if payload.name else None,
            role=payload.role,
        )
        return self._build_user_response(row)

    def update_password(
        self,
        current_user: dict,
        user_id: str,
        payload: UpdatePasswordRequest,
    ) -> None:
        if current_user["role"] != "admin" and current_user["id"] != user_id:
            raise AuthorizationError("Voce nao pode alterar a senha de outro usuario.")
        self.repository.update_password(
            user_id=user_id,
            company_id=current_user["company_id"],
            password_hash=hash_password(payload.password),
        )

    def update_user_status(
        self,
        current_user: dict,
        user_id: str,
        payload: UpdateUserStatusRequest,
    ) -> UserResponse:
        self._ensure_admin(current_user)
        row = self.repository.set_user_status(
            user_id=user_id,
            company_id=current_user["company_id"],
            is_active=payload.is_active,
        )
        return self._build_user_response(row)

    def _ensure_admin(self, current_user: dict) -> None:
        if current_user["role"] != "admin":
            raise AuthorizationError("Apenas administradores podem executar esta acao.")

    def _build_user_response(self, row: dict) -> UserResponse:
        return UserResponse(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            company=CompanySummary(
                id=row["company_id"],
                name=row["company_name"],
            ),
        )


user_service = UserService()
