from __future__ import annotations

from datetime import UTC, datetime

from app.services.assistant import AssistantService


def test_get_session_history_scopes_lookup_to_current_user() -> None:
    service = AssistantService()
    captured: dict[str, object] = {}

    class FakeRepository:
        def get_session_messages(self, **kwargs):
            captured.update(kwargs)
            return [
                {
                    "role": "human",
                    "content": "O que e DRE?",
                    "created_at": datetime(2026, 5, 6, 10, 0, tzinfo=UTC),
                    "sources": [],
                    "confidence_hint": None,
                }
            ]

    service.repository = FakeRepository()
    current_user = {
        "id": "user-1",
        "company_id": "company-1",
    }

    response = service.get_session_history("session-1", current_user)

    assert captured["session_id"] == "session-1"
    assert captured["owner_user_id"] == "user-1"
    assert captured["company_id"] == "company-1"
    assert response.session_id == "session-1"
    assert response.messages[0].content == "O que e DRE?"


def test_store_turn_persists_owner_scope() -> None:
    service = AssistantService()
    captured: dict[str, object] = {}

    class FakeRepository:
        def save_turn(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

    service.repository = FakeRepository()
    current_user = {
        "id": "user-1",
        "company_id": "company-1",
    }

    service._store_turn(
        "session-1",
        current_user,
        "Preciso revisar o fluxo financeiro.",
        "Vamos revisar.",
        sources=[{"filename": "manual.txt", "source_label": "manual.txt#chunk-0"}],
        confidence_hint="medium",
    )

    assert captured["args"] == (
        "session-1",
        "user-1",
        "company-1",
        "Preciso revisar o fluxo financeiro.",
        "Vamos revisar.",
    )
    assert captured["kwargs"]["confidence_hint"] == "medium"

