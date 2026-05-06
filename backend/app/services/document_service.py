from __future__ import annotations

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetail,
    DocumentListResponse,
    DocumentSummary,
)
from app.services.document_parser import document_parser
from app.services.embeddings import embedding_service


class DocumentService:
    def __init__(self) -> None:
        self.repository = DocumentRepository()

    async def upload_document(self, file: UploadFile) -> DocumentDetail:
        filename = (file.filename or "").strip()
        if not filename:
            raise ValidationError("O arquivo enviado precisa ter um nome valido.")

        payload = await file.read()
        await file.close()

        self._validate_upload_size(len(payload))
        content_type, extracted_text = document_parser.parse(filename, payload)
        chunks = self._build_chunks(
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
        )
        document = self.repository.create_document_with_chunks(
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
            chunks=chunks,
        )
        return DocumentDetail.model_validate(document)

    def list_documents(self) -> DocumentListResponse:
        documents = [
            DocumentSummary.model_validate(doc)
            for doc in self.repository.list_documents()
        ]
        return DocumentListResponse(documents=documents)

    def get_document(self, document_id: str) -> DocumentDetail:
        return DocumentDetail.model_validate(self.repository.get_document(document_id))

    def delete_document(self, document_id: str) -> DocumentDeleteResponse:
        self.repository.delete_document(document_id)
        return DocumentDeleteResponse(
            document_id=document_id,
            message="Documento removido com sucesso.",
        )

    def reindex_document(self, document_id: str) -> DocumentDetail:
        document = self.repository.get_document_text(document_id)
        chunks = self._build_chunks(
            filename=document["filename"],
            content_type=document["content_type"],
            extracted_text=document["extracted_text"],
        )
        updated_document = self.repository.replace_document_chunks(
            document_id,
            content_type=document["content_type"],
            extracted_text=document["extracted_text"],
            chunks=chunks,
        )
        return DocumentDetail.model_validate(updated_document)

    def _build_chunks(
        self,
        *,
        filename: str,
        content_type: str,
        extracted_text: str,
    ) -> list[dict[str, object]]:
        settings = get_settings()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.document_chunk_size,
            chunk_overlap=settings.document_chunk_overlap,
        )
        chunk_texts = [
            chunk.strip()
            for chunk in splitter.split_text(extracted_text)
            if chunk.strip()
        ]
        embeddings = embedding_service.embed_documents(chunk_texts)

        return [
            {
                "chunk_index": index,
                "content": text,
                "embedding": embeddings[index],
                "metadata_json": {
                    "filename": filename,
                    "content_type": content_type,
                },
            }
            for index, text in enumerate(chunk_texts)
        ]

    def _validate_upload_size(self, size_bytes: int) -> None:
        settings = get_settings()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValidationError(
                "O arquivo excede o limite permitido para upload. "
                f"Limite atual: {settings.max_upload_size_mb} MB."
            )


document_service = DocumentService()
