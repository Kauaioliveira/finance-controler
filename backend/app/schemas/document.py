from datetime import datetime

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: str
    filename: str
    content_type: str
    source_type: str
    status: str
    chunk_count: int
    word_count: int
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentSummary):
    preview: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class DocumentDeleteResponse(BaseModel):
    document_id: str
    message: str
