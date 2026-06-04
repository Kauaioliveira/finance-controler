from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import BytesIO

from fastapi import UploadFile

import app.services.finance_service as finance_service_module
from app.schemas.finance import FinanceTransaction
from app.services.finance_parser import RawFinanceTransaction
from app.services.finance_service import FinanceService


def test_categorize_transaction_prefers_csv_hint() -> None:
    service = FinanceService()
    raw = RawFinanceTransaction(
        row_number=2,
        date="2026-04-09",
        description="Pagamento folha operacional",
        amount=5400.0,
        direction="expense",
        category_hint="payroll",
    )

    transaction = service._categorize_transaction(raw)

    assert transaction.category == "payroll"
    assert transaction.category_label == "Folha e pessoas"
    assert transaction.confidence == 0.98
    assert transaction.notes == "Categoria reaproveitada do arquivo importado."


def test_categorize_transaction_falls_back_to_miscellaneous_when_rule_is_missing() -> None:
    service = FinanceService()
    raw = RawFinanceTransaction(
        row_number=3,
        date="2026-04-10",
        description="Compra inesperada sem padrao catalogado",
        amount=321.89,
        direction="expense",
        category_hint=None,
    )

    transaction = service._categorize_transaction(raw)

    assert transaction.category == "miscellaneous"
    assert transaction.confidence == 0.55
    assert "revisar manualmente" in (transaction.notes or "")


def test_build_insights_flags_uncategorized_transactions() -> None:
    service = FinanceService()
    transactions = [
        FinanceTransaction(
            row_number=2,
            date="2026-04-09",
            description="Pagamento folha operacional",
            amount=5400.0,
            direction="expense",
            category="payroll",
            category_label="Folha e pessoas",
            confidence=0.9,
        ),
        FinanceTransaction(
            row_number=3,
            date="2026-04-10",
            description="Compra inesperada sem padrao catalogado",
            amount=321.89,
            direction="expense",
            category="miscellaneous",
            category_label="Diversos",
            confidence=0.55,
            notes="Sem regra especifica; revisar manualmente.",
        ),
        FinanceTransaction(
            row_number=4,
            date="2026-04-12",
            description="Recebimento cliente premium",
            amount=9500.0,
            direction="income",
            category="sales_revenue",
            category_label="Receita de vendas",
            confidence=0.9,
        ),
    ]

    summary = service._build_summary_from_preview(transactions)
    categories = service._build_category_breakdown_from_preview(transactions, summary.total_expenses)
    monthly = service._build_monthly_summary_from_preview(transactions)
    insights = service._build_insights(summary, categories, monthly)

    assert summary.uncategorized_count == 1
    assert any(item.title == "Itens para revisar" for item in insights)


def test_create_import_persists_bundle_atomically(monkeypatch) -> None:
    service = FinanceService()
    captured: dict[str, object] = {}

    class FakeRepository:
        def persist_import_bundle(self, **kwargs):
            captured.update(kwargs)
            now = datetime(2026, 5, 6, 11, 0, tzinfo=UTC)
            return {
                "id": kwargs["import_id"],
                "company_id": kwargs["company_id"],
                "uploaded_by_user_id": kwargs["uploaded_by_user_id"],
                "uploaded_by_user_name": "Administrador",
                "filename": kwargs["filename"],
                "source_type": kwargs["source_type"],
                "status": kwargs["status"],
                "currency": kwargs["currency"],
                "total_rows": kwargs["total_rows"],
                "processed_rows": kwargs["processed_rows"],
                "error_message": None,
                "created_at": now,
                "updated_at": now,
                "finalized_at": None,
                "summary_json": kwargs["summary_json"],
                "categories_json": kwargs["categories_json"],
                "insights_json": kwargs["insights_json"],
            }

        def create_import(self, **kwargs):  # pragma: no cover - regression guard
            raise AssertionError("create_import nao deveria ser chamado isoladamente.")

        def create_transactions(self, **kwargs):  # pragma: no cover - regression guard
            raise AssertionError("create_transactions nao deveria ser chamado isoladamente.")

        def create_snapshot(self, **kwargs):  # pragma: no cover - regression guard
            raise AssertionError("create_snapshot nao deveria ser chamado isoladamente.")

        def update_import_status(self, **kwargs):  # pragma: no cover - regression guard
            raise AssertionError("update_import_status nao deveria ser chamado isoladamente.")

    async def fake_build_report_from_persisted(*, filename, currency, transactions):
        assert filename == "transactions.csv"
        assert currency == "BRL"
        assert len(transactions) == 1
        summary = service._build_summary_from_persisted(transactions)
        categories = service._build_category_breakdown_from_persisted(
            transactions,
            summary.total_expenses,
        )
        monthly = service._build_monthly_summary_from_persisted(transactions)
        insights = service._build_insights(summary, categories, monthly)
        return {
            "generated_at": datetime(2026, 5, 6, 11, 0, tzinfo=UTC),
            "filename": filename,
            "currency": currency,
            "summary": summary,
            "categories": categories,
            "monthly": monthly,
            "top_transactions": transactions,
            "insights": insights,
            "narrative": "Resumo persistido.",
        }

    service.repository = FakeRepository()
    monkeypatch.setattr(
        finance_service_module.finance_parser,
        "parse_csv",
        lambda filename, payload: [
            RawFinanceTransaction(
                row_number=1,
                date="2026-04-12",
                description="Recebimento cliente enterprise",
                amount=12000.0,
                direction="income",
                category_hint=None,
            )
        ],
    )
    monkeypatch.setattr(service, "_build_report_from_persisted", fake_build_report_from_persisted)

    upload = UploadFile(filename="transactions.csv", file=BytesIO(b"ignored"))
    current_user = {
        "id": "user-admin-1",
        "company_id": "company-1",
        "role": "admin",
    }

    response = asyncio.run(service.create_import(current_user, upload))

    assert captured["company_id"] == "company-1"
    assert captured["uploaded_by_user_id"] == "user-admin-1"
    assert captured["status"] == "processed"
    assert captured["processed_rows"] == 1
    assert len(captured["transactions"]) == 1
    assert captured["transactions"][0]["id"]
    assert response.filename == "transactions.csv"
    assert response.summary_preview is not None
    assert response.summary_preview.summary.transaction_count == 1
