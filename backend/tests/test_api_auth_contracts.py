from __future__ import annotations

from app.api import routes
from app.main import app
from app.schemas.auth import AuthTokenResponse

from .conftest import override_current_user


def test_health_and_config_expose_runtime_metadata(client) -> None:
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "schema_ready": True,
        "detail": "Mocked PostgreSQL pronto.",
    }

    config_response = client.get("/config")
    assert config_response.status_code == 200
    payload = config_response.json()
    assert payload["supported_roles"] == ["admin", "analyst", "viewer"]
    assert payload["supported_finance_extensions"] == [".csv"]
    assert payload["database_ready"] is True


def test_login_returns_token_payload(
    client,
    monkeypatch,
    auth_token_response: AuthTokenResponse,
) -> None:
    monkeypatch.setattr(
        routes.auth_service,
        "login",
        lambda *, email, password: auth_token_response,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "admin@finance-controler.local",
            "password": "Admin123!",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "access-token-123"
    assert payload["refresh_token"] == "refresh-token-123"
    assert payload["user"]["role"] == "admin"


def test_login_validation_error_uses_standard_contract(client) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": "a",
            "password": "123",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "request_validation_error"
    fields = {item["field"] for item in payload["field_errors"]}
    assert "body.email" in fields
    assert "body.password" in fields


def test_protected_route_without_token_returns_auth_error(client) -> None:
    response = client.get("/finance/categories")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Token de acesso ausente.",
        "code": "authentication_error",
    }


def test_auth_me_returns_current_user_summary(client, admin_user_dict) -> None:
    override_current_user(admin_user_dict)

    response = client.get("/auth/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@finance-controler.local"
    assert payload["company"]["name"] == "Finance Controler"
