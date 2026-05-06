from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.exceptions import AuthorizationError
from app.schemas.user import (
    CreateUserRequest,
    UpdatePasswordRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
)
from app.services.user_service import UserService
import app.services.user_service as user_service_module


def _user_row() -> dict[str, object]:
    now = datetime(2026, 5, 5, 12, 0, tzinfo=UTC)
    return {
        "id": "user-1",
        "name": "Maria Financeiro",
        "email": "maria@finance-controler.local",
        "role": "analyst",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "company_id": "company-1",
        "company_name": "Finance Controler",
    }


def _admin_user() -> dict[str, object]:
    return {
        "id": "admin-1",
        "role": "admin",
        "company_id": "company-1",
    }


def _viewer_user() -> dict[str, object]:
    return {
        "id": "viewer-1",
        "role": "viewer",
        "company_id": "company-1",
    }


def test_list_users_returns_paginated_response() -> None:
    service = UserService()

    class FakeRepository:
        def list_users(self, company_id: str, *, limit: int, offset: int) -> list[dict[str, object]]:
            assert company_id == "company-1"
            assert limit == 20
            assert offset == 0
            return [_user_row()]

        def count_users(self, company_id: str) -> int:
            return 1

    service.repository = FakeRepository()

    response = service.list_users(_admin_user(), page=1, page_size=20)

    assert response.total == 1
    assert response.items[0].email == "maria@finance-controler.local"


def test_create_user_hashes_password_and_normalizes_email(monkeypatch: pytest.MonkeyPatch) -> None:
    service = UserService()
    captured: dict[str, object] = {}

    class FakeRepository:
        def create_user(self, **kwargs) -> dict[str, object]:
            captured.update(kwargs)
            return {
                **_user_row(),
                "name": kwargs["name"],
                "email": kwargs["email"],
                "role": kwargs["role"],
            }

    service.repository = FakeRepository()
    monkeypatch.setattr(user_service_module, "hash_password", lambda password: "hashed-password")

    payload = CreateUserRequest(
        name="  Maria Financeiro  ",
        email="MARIA@Finance-Controler.Local ",
        role="analyst",
        password="SenhaInicial123",
    )
    response = service.create_user(_admin_user(), payload)

    assert response.email == "maria@finance-controler.local"
    assert captured["password_hash"] == "hashed-password"
    assert captured["name"] == "Maria Financeiro"


def test_update_password_allows_self_service(monkeypatch: pytest.MonkeyPatch) -> None:
    service = UserService()
    updated: dict[str, object] = {}

    class FakeRepository:
        def update_password(self, **kwargs) -> None:
            updated.update(kwargs)

    service.repository = FakeRepository()
    monkeypatch.setattr(user_service_module, "hash_password", lambda password: "hashed-password")

    service.update_password(
        {"id": "viewer-1", "role": "viewer", "company_id": "company-1"},
        "viewer-1",
        UpdatePasswordRequest(password="NovaSenha123"),
    )

    assert updated["user_id"] == "viewer-1"
    assert updated["password_hash"] == "hashed-password"


def test_update_password_blocks_other_non_admin_users() -> None:
    service = UserService()

    with pytest.raises(AuthorizationError) as error:
        service.update_password(
            _viewer_user(),
            "admin-1",
            UpdatePasswordRequest(password="NovaSenha123"),
        )

    assert error.value.detail == "Voce nao pode alterar a senha de outro usuario."


def test_update_user_status_requires_admin() -> None:
    service = UserService()

    with pytest.raises(AuthorizationError) as error:
        service.update_user_status(
            _viewer_user(),
            "user-1",
            UpdateUserStatusRequest(is_active=False),
        )

    assert error.value.detail == "Apenas administradores podem executar esta acao."


def test_update_user_returns_serialized_profile() -> None:
    service = UserService()

    class FakeRepository:
        def update_user(self, **kwargs) -> dict[str, object]:
            return {
                **_user_row(),
                "name": kwargs["name"],
                "role": kwargs["role"],
            }

    service.repository = FakeRepository()

    response = service.update_user(
        _admin_user(),
        "user-1",
        UpdateUserRequest(name="Maria Lider", role="viewer"),
    )

    assert response.name == "Maria Lider"
    assert response.role == "viewer"
