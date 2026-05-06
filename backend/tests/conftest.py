from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api import dependencies
from app.main import app
from app.schemas.auth import AuthTokenResponse, AuthUserResponse, CompanySummary
from app.schemas.finance import (
    FinanceCategoryBreakdown,
    FinanceImportResponse,
    FinanceImportSummaryPreview,
    FinanceInsight,
    FinanceMonthlySummary,
    FinancePersistedTransaction,
    FinanceReportResponse,
    FinanceSummary,
)
from app.schemas.user import UserListResponse, UserResponse
from app.services.assistant import assistant_service


@pytest.fixture(autouse=True)
def isolate_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant_service, "initialize", lambda: None)
    monkeypatch.setattr(
        assistant_service,
        "get_system_status",
        lambda: {
            "status": "ok",
            "schema_ready": True,
            "detail": "Mocked PostgreSQL pronto.",
        },
    )
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_user_dict() -> dict[str, object]:
    return {
        "id": "user-admin-1",
        "name": "Administrador",
        "email": "admin@finance-controler.local",
        "role": "admin",
        "is_active": True,
        "company_id": "company-1",
        "company_name": "Finance Controler",
    }


@pytest.fixture
def analyst_user_dict() -> dict[str, object]:
    return {
        "id": "user-analyst-1",
        "name": "Analista",
        "email": "analyst@finance-controler.local",
        "role": "analyst",
        "is_active": True,
        "company_id": "company-1",
        "company_name": "Finance Controler",
    }


@pytest.fixture
def viewer_user_dict() -> dict[str, object]:
    return {
        "id": "user-viewer-1",
        "name": "Viewer",
        "email": "viewer@finance-controler.local",
        "role": "viewer",
        "is_active": True,
        "company_id": "company-1",
        "company_name": "Finance Controler",
    }


@pytest.fixture
def auth_user_response(admin_user_dict: dict[str, object]) -> AuthUserResponse:
    return AuthUserResponse(
        id=str(admin_user_dict["id"]),
        name=str(admin_user_dict["name"]),
        email=str(admin_user_dict["email"]),
        role=str(admin_user_dict["role"]),
        is_active=bool(admin_user_dict["is_active"]),
        company=CompanySummary(
            id=str(admin_user_dict["company_id"]),
            name=str(admin_user_dict["company_name"]),
        ),
    )


@pytest.fixture
def auth_token_response(auth_user_response: AuthUserResponse) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token="access-token-123",
        refresh_token="refresh-token-123",
        user=auth_user_response,
    )


@pytest.fixture
def sample_user_list() -> UserListResponse:
    now = datetime(2026, 5, 5, 12, 0, tzinfo=UTC)
    company = CompanySummary(id="company-1", name="Finance Controler")
    return UserListResponse(
        items=[
            UserResponse(
                id="user-admin-1",
                name="Administrador",
                email="admin@finance-controler.local",
                role="admin",
                is_active=True,
                created_at=now,
                updated_at=now,
                company=company,
            )
        ],
        total=1,
        page=1,
        page_size=20,
    )


@pytest.fixture
def sample_import_response() -> FinanceImportResponse:
    now = datetime(2026, 5, 5, 12, 0, tzinfo=UTC)
    summary = FinanceSummary(
        total_income=22442.55,
        total_expenses=12047.50,
        net_balance=10395.05,
        transaction_count=10,
        categorized_count=10,
        uncategorized_count=0,
    )
    preview = FinanceImportSummaryPreview(
        summary=summary,
        categories=[
            FinanceCategoryBreakdown(
                category="payroll",
                label="Folha e pessoas",
                direction="expense",
                total_amount=5400.0,
                net_amount=-5400.0,
                transaction_count=1,
                share=0.4482,
            )
        ],
        insights=[
            FinanceInsight(
                title="Caixa operacional positivo",
                detail="O periodo fechou com saldo positivo.",
                tone="positive",
            )
        ],
    )
    return FinanceImportResponse(
        id="import-1",
        company_id="company-1",
        uploaded_by_user_id="user-admin-1",
        uploaded_by_user_name="Administrador",
        filename="transactions-sample.csv",
        source_type="csv",
        status="processed",
        currency="BRL",
        total_rows=10,
        processed_rows=10,
        error_message=None,
        created_at=now,
        updated_at=now,
        finalized_at=None,
        summary_preview=preview,
    )


@pytest.fixture
def sample_persisted_transaction() -> FinancePersistedTransaction:
    return FinancePersistedTransaction(
        id="txn-1",
        row_number=2,
        transaction_date="2026-04-09",
        description="Pagamento folha operacional",
        amount=5400.0,
        direction="expense",
        predicted_category="payroll",
        predicted_category_label="Folha e pessoas",
        final_category="payroll",
        final_category_label="Folha e pessoas",
        category_confidence=0.9,
        review_notes="Conferido pelo financeiro.",
        reviewed_at=datetime(2026, 5, 5, 12, 30, tzinfo=UTC),
        reviewed_by_user_id="user-admin-1",
    )


@pytest.fixture
def sample_report_response(
    sample_persisted_transaction: FinancePersistedTransaction,
) -> FinanceReportResponse:
    summary = FinanceSummary(
        total_income=22442.55,
        total_expenses=12047.50,
        net_balance=10395.05,
        transaction_count=10,
        categorized_count=10,
        uncategorized_count=0,
    )
    return FinanceReportResponse(
        import_id="import-1",
        generated_at=datetime(2026, 5, 5, 12, 45, tzinfo=UTC),
        currency="BRL",
        summary=summary,
        categories=[
            FinanceCategoryBreakdown(
                category="payroll",
                label="Folha e pessoas",
                direction="expense",
                total_amount=5400.0,
                net_amount=-5400.0,
                transaction_count=1,
                share=0.4482,
            )
        ],
        monthly=[
            FinanceMonthlySummary(
                month="2026-04",
                income=22442.55,
                expenses=12047.50,
                net=10395.05,
            )
        ],
        top_transactions=[sample_persisted_transaction],
        insights=[
            FinanceInsight(
                title="Caixa operacional positivo",
                detail="O periodo analisado fechou com saldo positivo.",
                tone="positive",
            )
        ],
        narrative="Relatorio consolidado para fechamento financeiro.",
    )


def override_current_user(user: dict[str, object]) -> None:
    app.dependency_overrides[dependencies.get_current_user] = lambda: user
