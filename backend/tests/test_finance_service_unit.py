from __future__ import annotations

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
