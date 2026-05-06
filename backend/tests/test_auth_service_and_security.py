from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.services.auth_service import AuthService
import app.services.auth_service as auth_service_module


def _user_row(*, is_active: bool = True) -> dict[str, object]:
    return {
        "id": "user-admin-1",
        "name": "Administrador",
        "email": "admin@finance-controler.local",
        "role": "admin",
        "is_active": is_active,
        "company_id": "company-1",
        "company_name": "Finance Controler",
        "password_hash": "hashed-password",
    }


def test_password_hash_and_verify_roundtrip() -> None:
    password_hash = hash_password("Admin123!")

    assert password_hash != "Admin123!"
    assert verify_password("Admin123!", password_hash) is True
    assert verify_password("SenhaErrada!", password_hash) is False


def test_access_token_can_be_created_and_decoded() -> None:
    token = create_access_token(
        user_id="user-admin-1",
        company_id="company-1",
        role="admin",
    )

    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == "user-admin-1"
    assert payload["company_id"] == "company-1"
    assert payload["type"] == "access"


def test_refresh_token_can_be_hashed_and_decoded() -> None:
    token, session_id, expires_at = create_refresh_token(
        user_id="user-admin-1",
        company_id="company-1",
        role="admin",
    )

    payload = decode_token(token, expected_type="refresh")

    assert payload["sid"] == session_id
    assert hash_refresh_token(token) != token
    assert expires_at > datetime.now(UTC) + timedelta(days=6)


def test_decode_token_rejects_wrong_token_type() -> None:
    token = create_access_token(
        user_id="user-admin-1",
        company_id="company-1",
        role="admin",
    )

    with pytest.raises(AuthenticationError) as error:
        decode_token(token, expected_type="refresh")

    assert error.value.detail == "Tipo de token invalido."


def test_auth_service_login_creates_session(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()
    created_session: dict[str, object] = {}
    touched_users: list[str] = []

    class FakeUserRepository:
        def get_user_by_email(self, email: str) -> dict[str, object]:
            assert email == "admin@finance-controler.local"
            return _user_row()

        def touch_last_login(self, user_id: str) -> None:
            touched_users.append(user_id)

    class FakeSessionRepository:
        def create_session(self, **kwargs) -> None:
            created_session.update(kwargs)

    service.user_repository = FakeUserRepository()
    service.session_repository = FakeSessionRepository()

    monkeypatch.setattr(auth_service_module, "verify_password", lambda password, password_hash: True)
    monkeypatch.setattr(auth_service_module, "create_access_token", lambda **kwargs: "access-token")
    monkeypatch.setattr(
        auth_service_module,
        "create_refresh_token",
        lambda **kwargs: ("refresh-token", "session-123", datetime(2026, 5, 12, tzinfo=UTC)),
    )
    monkeypatch.setattr(auth_service_module, "hash_refresh_token", lambda token: "refresh-hash")

    response = service.login(
        email="admin@finance-controler.local",
        password="Admin123!",
    )

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    assert response.user.email == "admin@finance-controler.local"
    assert created_session["session_id"] == "session-123"
    assert created_session["refresh_token_hash"] == "refresh-hash"
    assert touched_users == ["user-admin-1"]


def test_auth_service_login_rejects_invalid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()

    class FakeUserRepository:
        def get_user_by_email(self, email: str) -> dict[str, object]:
            return _user_row()

    service.user_repository = FakeUserRepository()
    monkeypatch.setattr(auth_service_module, "verify_password", lambda password, password_hash: False)

    with pytest.raises(AuthenticationError) as error:
        service.login(email="admin@finance-controler.local", password="SenhaErrada!")

    assert error.value.detail == "Email ou senha invalidos."


def test_auth_service_refresh_rotates_existing_session(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()
    rotated: dict[str, object] = {}

    class FakeUserRepository:
        def get_user_by_id(self, user_id: str) -> dict[str, object]:
            return _user_row()

    class FakeSessionRepository:
        def get_session(self, session_id: str) -> dict[str, object]:
            return {
                "user_id": "user-admin-1",
                "revoked_at": None,
                "refresh_token_hash": "refresh-hash",
            }

        def rotate_session(self, **kwargs) -> None:
            rotated.update(kwargs)

    service.user_repository = FakeUserRepository()
    service.session_repository = FakeSessionRepository()

    monkeypatch.setattr(
        auth_service_module,
        "decode_token",
        lambda token, expected_type: {
            "sid": "session-123",
            "sub": "user-admin-1",
            "type": "refresh",
        },
    )
    monkeypatch.setattr(auth_service_module, "hash_refresh_token", lambda token: "refresh-hash")
    monkeypatch.setattr(auth_service_module, "create_access_token", lambda **kwargs: "new-access-token")
    monkeypatch.setattr(
        auth_service_module,
        "create_refresh_token",
        lambda **kwargs: ("new-refresh-token", "session-123", datetime(2026, 5, 12, tzinfo=UTC)),
    )

    response = service.refresh("refresh-token")

    assert response.access_token == "new-access-token"
    assert response.refresh_token == "new-refresh-token"
    assert rotated["session_id"] == "session-123"
    assert rotated["refresh_token_hash"] == "refresh-hash"


def test_auth_service_logout_revokes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()
    revoked_sessions: list[str] = []

    class FakeSessionRepository:
        def revoke_session(self, session_id: str) -> None:
            revoked_sessions.append(session_id)

    service.session_repository = FakeSessionRepository()
    monkeypatch.setattr(
        auth_service_module,
        "decode_token",
        lambda token, expected_type: {
            "sid": "session-123",
            "sub": "user-admin-1",
            "type": "refresh",
        },
    )

    service.logout("refresh-token")

    assert revoked_sessions == ["session-123"]


def test_authenticate_access_token_rejects_inactive_user(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()

    class FakeUserRepository:
        def get_user_by_id(self, user_id: str) -> dict[str, object]:
            return _user_row(is_active=False)

    service.user_repository = FakeUserRepository()
    monkeypatch.setattr(
        auth_service_module,
        "decode_token",
        lambda token, expected_type: {
            "sub": "user-admin-1",
            "type": "access",
        },
    )

    with pytest.raises(AuthenticationError) as error:
        service.authenticate_access_token("access-token")

    assert error.value.detail == "Usuario inativo."
