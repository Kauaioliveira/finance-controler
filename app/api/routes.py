from fastapi import APIRouter, File, UploadFile

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.schemas.chat import ChatRequest, ChatResponse, SessionHistoryResponse
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetail,
    DocumentListResponse,
)
from app.services.assistant import assistant_service
from app.services.document_parser import SUPPORTED_DOCUMENT_EXTENSIONS
from app.services.document_service import document_service


router = APIRouter()


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
    }


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.message.strip():
        raise ValidationError("A mensagem nao pode ser vazia.")

    return await assistant_service.ask(payload)


@router.get(
    "/sessions/{session_id}/history",
    response_model=SessionHistoryResponse,
    tags=["chat"],
)
async def session_history(session_id: str) -> SessionHistoryResponse:
    return assistant_service.get_session_history(session_id)


@router.post(
    "/documents/upload",
    response_model=DocumentDetail,
    tags=["documents"],
)
async def upload_document(file: UploadFile = File(...)) -> DocumentDetail:
    return await document_service.upload_document(file)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    tags=["documents"],
)
async def list_documents() -> DocumentListResponse:
    return document_service.list_documents()


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetail,
    tags=["documents"],
)
async def get_document(document_id: str) -> DocumentDetail:
    return document_service.get_document(document_id)


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    tags=["documents"],
)
async def delete_document(document_id: str) -> DocumentDeleteResponse:
    return document_service.delete_document(document_id)


@router.post(
    "/documents/{document_id}/reindex",
    response_model=DocumentDetail,
    tags=["documents"],
)
async def reindex_document(document_id: str) -> DocumentDetail:
    return document_service.reindex_document(document_id)
