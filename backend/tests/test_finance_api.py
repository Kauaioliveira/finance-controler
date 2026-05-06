from __future__ import annotations

from app.api import routes

from .conftest import override_current_user


def test_admin_can_list_users(
    client,
    monkeypatch,
    admin_user_dict,
    sample_user_list,
) -> None:
    override_current_user(admin_user_dict)
    monkeypatch.setattr(
        routes.user_service,
        "list_users",
        lambda current_user, *, page, page_size: sample_user_list,
    )

    response = client.get("/users?page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["role"] == "admin"


def test_viewer_cannot_list_users(client, viewer_user_dict) -> None:
    override_current_user(viewer_user_dict)

    response = client.get("/users")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Voce nao tem permissao para acessar este recurso.",
        "code": "authorization_error",
    }


def test_create_finance_import_returns_persisted_payload(
    client,
    monkeypatch,
    admin_user_dict,
    sample_import_response,
) -> None:
    override_current_user(admin_user_dict)

    async def fake_create_import(current_user, file):
        assert current_user["role"] == "admin"
        assert file.filename == "transactions-sample.csv"
        return sample_import_response

    monkeypatch.setattr(routes.finance_service, "create_import", fake_create_import)

    response = client.post(
        "/finance/imports",
        files={"file": ("transactions-sample.csv", b"date,description,amount\n", "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "transactions-sample.csv"
    assert payload["status"] == "processed"
    assert payload["summary_preview"]["summary"]["net_balance"] == 10395.05


def test_patch_finance_transaction_returns_reviewed_payload(
    client,
    monkeypatch,
    analyst_user_dict,
    sample_persisted_transaction,
) -> None:
    override_current_user(analyst_user_dict)

    async def fake_update_transaction(current_user, import_id, transaction_id, payload):
        assert current_user["role"] == "analyst"
        assert import_id == "import-1"
        assert transaction_id == "txn-1"
        assert payload.final_category == "payroll"
        return sample_persisted_transaction

    monkeypatch.setattr(routes.finance_service, "update_transaction", fake_update_transaction)

    response = client.patch(
        "/finance/imports/import-1/transactions/txn-1",
        json={
            "final_category": "payroll",
            "review_notes": "Conferido pelo financeiro.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["final_category"] == "payroll"
    assert payload["review_notes"] == "Conferido pelo financeiro."


def test_finalize_import_blocks_viewer_role(client, viewer_user_dict) -> None:
    override_current_user(viewer_user_dict)

    response = client.post("/finance/imports/import-1/finalize")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Voce nao tem permissao para acessar este recurso.",
        "code": "authorization_error",
    }


def test_get_finance_report_returns_snapshot_payload(
    client,
    monkeypatch,
    admin_user_dict,
    sample_report_response,
) -> None:
    override_current_user(admin_user_dict)
    monkeypatch.setattr(
        routes.finance_service,
        "get_report",
        lambda current_user, import_id: sample_report_response,
    )

    response = client.get("/finance/imports/import-1/report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["import_id"] == "import-1"
    assert payload["summary"]["transaction_count"] == 10
    assert payload["top_transactions"][0]["description"] == "Pagamento folha operacional"
