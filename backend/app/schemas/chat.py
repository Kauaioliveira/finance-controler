from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Pergunta do usuario.")
    session_id: str = Field(
        default="default-session",
        min_length=1,
        description="Identificador da conversa.",
    )


class ChatSource(BaseModel):
    filename: str
    source_label: str
    document_id: str | None = None
    chunk_index: int | None = None
    excerpt: str | None = None
    score: float | None = Field(default=None, ge=0, le=1)


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    used_demo_mode: bool
    sources: list[ChatSource] = Field(default_factory=list)
    confidence_hint: Literal["low", "medium", "high"]


class HistoryMessage(BaseModel):
    role: str
    content: str
    created_at: datetime
    sources: list[ChatSource] = Field(default_factory=list)
    confidence_hint: Literal["low", "medium", "high"] | None = None


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryMessage]
