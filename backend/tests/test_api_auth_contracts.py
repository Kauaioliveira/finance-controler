from __future__ import annotations

from datetime import UTC, datetime

from app.api import routes
from app.main import app
from app.schemas.auth import AuthTokenResponse
from app.schemas.chat import ChatResponse, HistoryMessage, SessionHistoryResponse

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


def test_chat_forwards_authenticated_user_to_assistant_service(
    client,
    monkeypatch,
    analyst_user_dict,
) -> None:
    override_current_user(analyst_user_dict)
    captured: dict[str, object] = {}

    async def fake_ask(payload, current_user):
        captured["session_id"] = payload.session_id
        captured["message"] = payload.message
        captured["current_user"] = current_user
        return ChatResponse(
            answer="Resposta segura.",
            session_id=payload.session_id,
            used_demo_mode=False,
            sources=[],
            confidence_hint="low",
        )

    monkeypatch.setattr(routes.assistant_service, "ask", fake_ask)

    response = client.post(
        "/chat",
        json={
            "message": "Explique a DRE do periodo.",
            "session_id": "session-analyst-1",
        },
    )

    assert response.status_code == 200
    assert captured["session_id"] == "session-analyst-1"
    assert captured["message"] == "Explique a DRE do periodo."
    assert captured["current_user"]["id"] == analyst_user_dict["id"]
    assert captured["current_user"]["company_id"] == analyst_user_dict["company_id"]


def test_session_history_forwards_authenticated_user_to_assistant_service(
    client,
    monkeypatch,
    analyst_user_dict,
) -> None:
    override_current_user(analyst_user_dict)
    captured: dict[str, object] = {}

    def fake_get_session_history(session_id, current_user):
        captured["session_id"] = session_id
        captured["current_user"] = current_user
        return SessionHistoryResponse(
            session_id=session_id,
            messages=[
                HistoryMessage(
                    role="ai",
                    content="Historico protegido.",
                    created_at=datetime(2026, 5, 6, 10, 15, tzinfo=UTC),
                    sources=[],
                    confidence_hint="low",
                )
            ],
        )

    monkeypatch.setattr(
        routes.assistant_service,
        "get_session_history",
        fake_get_session_history,
    )

    response = client.get("/sessions/session-analyst-1/history")

    assert response.status_code == 200
    assert captured["session_id"] == "session-analyst-1"
    assert captured["current_user"]["id"] == analyst_user_dict["id"]
    assert captured["current_user"]["company_id"] == analyst_user_dict["company_id"]
