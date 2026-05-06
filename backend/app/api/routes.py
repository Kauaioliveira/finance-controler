from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.dependencies import get_current_user, require_roles
from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.schemas.auth import (
    AuthTokenResponse,
    AuthUserResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
)
from app.schemas.chat import ChatRequest, ChatResponse, SessionHistoryResponse
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetail,
    DocumentListResponse,
)
from app.schemas.finance import (
    FinalizeFinanceImportResponse,
    FinanceAnalysisResponse,
    FinanceCategoryCatalogResponse,
    FinanceImportListResponse,
    FinanceImportResponse,
    FinancePersistedTransaction,
    FinanceReportResponse,
    FinanceTransactionListResponse,
    UpdateFinanceTransactionRequest,
)
from app.schemas.user import (
    CreateUserRequest,
    UpdatePasswordRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserResponse,
)
from app.services.assistant import assistant_service
from app.services.auth_service import auth_service
from app.services.document_parser import SUPPORTED_DOCUMENT_EXTENSIONS
from app.services.document_service import document_service
from app.services.finance_service import finance_service
from app.services.user_service import user_service


router = APIRouter()


def _resolve_page_size(page_size: int) -> int:
    settings = get_settings()
    return max(1, min(page_size, settings.max_page_size))


@router.get("/health", tags=["health"])
async def health() -> dict[str, str | bool]:
    return assistant_service.get_system_status()


@router.get("/config", tags=["config"])
async def config() -> dict[str, str | bool | int | float | list[str]]:
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "debug": settings.app_debug,
        "demo_mode": settings.demo_mode,
        "max_chat_history": settings.max_chat_history,
        "model": settings.openai_model,
        "embeddings_model": settings.openai_embeddings_model,
        "database_ready": assistant_service.get_system_status()["schema_ready"],
        "rag_top_k": settings.rag_top_k,
        "rag_max_distance": settings.rag_max_distance,
        "allowed_origins": settings.allowed_origins_list,
        "max_upload_size_mb": settings.max_upload_size_mb,
        "supported_extensions": sorted(SUPPORTED_DOCUMENT_EXTENSIONS.keys()),
        "supported_finance_extensions": [".csv"],
        "supported_roles": ["admin", "analyst", "viewer"],
        "finance_statuses": ["uploaded", "processed", "in_review", "finalized", "failed"],
        "default_page_size": settings.default_page_size,
        "max_page_size": settings.max_page_size,
    }


@router.post("/auth/login", response_model=AuthTokenResponse, tags=["auth"])
async def login(payload: LoginRequest) -> AuthTokenResponse:
    return auth_service.login(email=payload.email, password=payload.password)


@router.post("/auth/refresh", response_model=AuthTokenResponse, tags=["auth"])
async def refresh(payload: RefreshRequest) -> AuthTokenResponse:
    return auth_service.refresh(payload.refresh_token)


@router.post("/auth/logout", tags=["auth"])
async def logout(payload: LogoutRequest) -> dict[str, str]:
    auth_service.logout(payload.refresh_token)
    return {"detail": "Sessao encerrada com sucesso."}


@router.get("/auth/me", response_model=AuthUserResponse, tags=["auth"])
async def me(current_user: dict = Depends(get_current_user)) -> AuthUserResponse:
    return auth_service.build_me(current_user)


@router.get("/users", response_model=UserListResponse, tags=["users"])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    current_user: dict = Depends(require_roles("admin")),
) -> UserListResponse:
    return user_service.list_users(
        current_user,
        page=page,
        page_size=_resolve_page_size(page_size),
    )


@router.post("/users", response_model=UserResponse, tags=["users"])
async def create_user(
    payload: CreateUserRequest,
    current_user: dict = Depends(require_roles("admin")),
) -> UserResponse:
    return user_service.create_user(current_user, payload)


@router.patch("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def patch_user(
    user_id: str,
    payload: UpdateUserRequest,
    current_user: dict = Depends(require_roles("admin")),
) -> UserResponse:
    return user_service.update_user(current_user, user_id, payload)


@router.patch("/users/{user_id}/password", tags=["users"])
async def patch_user_password(
    user_id: str,
    payload: UpdatePasswordRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    user_service.update_password(current_user, user_id, payload)
    return {"detail": "Senha atualizada com sucesso."}


@router.patch("/users/{user_id}/status", response_model=UserResponse, tags=["users"])
async def patch_user_status(
    user_id: str,
    payload: UpdateUserStatusRequest,
    current_user: dict = Depends(require_roles("admin")),
) -> UserResponse:
    return user_service.update_user_status(current_user, user_id, payload)


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    payload: ChatRequest,
    _: dict = Depends(get_current_user),
) -> ChatResponse:
    if not payload.message.strip():
        raise ValidationError("A mensagem nao pode ser vazia.")
    return await assistant_service.ask(payload)


@router.get(
    "/sessions/{session_id}/history",
    response_model=SessionHistoryResponse,
    tags=["chat"],
)
async def session_history(
    session_id: str,
    _: dict = Depends(get_current_user),
) -> SessionHistoryResponse:
    return assistant_service.get_session_history(session_id)


@router.post(
    "/documents/upload",
    response_model=DocumentDetail,
    tags=["documents"],
)
async def upload_document(
    file: UploadFile = File(...),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> DocumentDetail:
    return await document_service.upload_document(file)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    tags=["documents"],
)
async def list_documents(
    _: dict = Depends(get_current_user),
) -> DocumentListResponse:
    return document_service.list_documents()


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetail,
    tags=["documents"],
)
async def get_document(
    document_id: str,
    _: dict = Depends(get_current_user),
) -> DocumentDetail:
    return document_service.get_document(document_id)


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    tags=["documents"],
)
async def delete_document(
    document_id: str,
    _: dict = Depends(require_roles("admin", "analyst")),
) -> DocumentDeleteResponse:
    return document_service.delete_document(document_id)


@router.post(
    "/documents/{document_id}/reindex",
    response_model=DocumentDetail,
    tags=["documents"],
)
async def reindex_document(
    document_id: str,
    _: dict = Depends(require_roles("admin", "analyst")),
) -> DocumentDetail:
    return document_service.reindex_document(document_id)


@router.get(
    "/finance/categories",
    response_model=FinanceCategoryCatalogResponse,
    tags=["finance"],
)
async def list_finance_categories(
    _: dict = Depends(get_current_user),
) -> FinanceCategoryCatalogResponse:
    return finance_service.get_category_catalog()


@router.post(
    "/finance/analyze",
    response_model=FinanceAnalysisResponse,
    tags=["finance"],
    deprecated=True,
)
async def analyze_finance_file(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
) -> FinanceAnalysisResponse:
    return await finance_service.analyze_file_preview(file)


@router.get(
    "/finance/imports",
    response_model=FinanceImportListResponse,
    tags=["finance"],
)
async def list_finance_imports(
    status: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    uploaded_by_user_id: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    current_user: dict = Depends(get_current_user),
) -> FinanceImportListResponse:
    return finance_service.list_imports(
        current_user,
        page=page,
        page_size=_resolve_page_size(page_size),
        status=status,
        date_from=date_from,
        date_to=date_to,
        uploaded_by_user_id=uploaded_by_user_id,
    )


@router.post(
    "/finance/imports",
    response_model=FinanceImportResponse,
    tags=["finance"],
)
async def create_finance_import(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles("admin", "analyst")),
) -> FinanceImportResponse:
    return await finance_service.create_import(current_user, file)


@router.get(
    "/finance/imports/{import_id}",
    response_model=FinanceImportResponse,
    tags=["finance"],
)
async def get_finance_import(
    import_id: str,
    current_user: dict = Depends(get_current_user),
) -> FinanceImportResponse:
    return finance_service.get_import(current_user, import_id)


@router.get(
    "/finance/imports/{import_id}/transactions",
    response_model=FinanceTransactionListResponse,
    tags=["finance"],
)
async def get_finance_transactions(
    import_id: str,
    category: str | None = Query(default=None),
    query: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    current_user: dict = Depends(get_current_user),
) -> FinanceTransactionListResponse:
    return finance_service.get_transactions(
        current_user,
        import_id,
        page=page,
        page_size=_resolve_page_size(page_size),
        category=category,
        query=query,
    )


@router.patch(
    "/finance/imports/{import_id}/transactions/{transaction_id}",
    response_model=FinancePersistedTransaction,
    tags=["finance"],
)
async def patch_finance_transaction(
    import_id: str,
    transaction_id: str,
    payload: UpdateFinanceTransactionRequest,
    current_user: dict = Depends(require_roles("admin", "analyst")),
) -> FinancePersistedTransaction:
    return await finance_service.update_transaction(current_user, import_id, transaction_id, payload)


@router.post(
    "/finance/imports/{import_id}/finalize",
    response_model=FinalizeFinanceImportResponse,
    tags=["finance"],
)
async def finalize_finance_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin", "analyst")),
) -> FinalizeFinanceImportResponse:
    return await finance_service.finalize_import(current_user, import_id)


@router.get(
    "/finance/imports/{import_id}/report",
    response_model=FinanceReportResponse,
    tags=["finance"],
)
async def get_finance_report(
    import_id: str,
    current_user: dict = Depends(get_current_user),
) -> FinanceReportResponse:
    return finance_service.get_report(current_user, import_id)
