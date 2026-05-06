from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.repositories.chat_repository import ChatRepository
from app.repositories.database import database
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    HistoryMessage,
    SessionHistoryResponse,
)
from app.services.retrieval import retrieval_service


SYSTEM_PROMPT = """
Voce e um assistente para uma aplicacao de contabilidade.

Regras de comportamento:
- responda em portugues do Brasil
- use apenas o contexto documental fornecido como base principal
- cite o nome do arquivo quando o contexto sustentar a resposta
- se o contexto nao for suficiente, diga explicitamente que nao encontrou base documental confiavel
- seja conservador em temas fiscais, juridicos e contabeis sensiveis
- nao invente normas, aliquotas ou obrigacoes
""".strip()


class AssistantService:
    def __init__(self) -> None:
        self.repository = ChatRepository()

    def initialize(self) -> None:
        database.initialize()

    async def ask(self, payload: ChatRequest) -> ChatResponse:
        settings = get_settings()
        history = self._get_history_messages(payload.session_id)

        if settings.demo_mode:
            answer = self._build_demo_answer(payload.message)
            self._store_turn(
                payload.session_id,
                payload.message,
                answer,
                sources=[],
                confidence_hint="low",
            )
            return ChatResponse(
                answer=answer,
                session_id=payload.session_id,
                used_demo_mode=True,
                sources=[],
                confidence_hint="low",
            )

        retrieval = retrieval_service.search(payload.message)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("system", "Contexto documental recuperado:\n{knowledge_context}"),
                *self._history_as_tuples(history),
                ("human", "{input}"),
            ]
        )

        model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
        )

        chain = prompt | model
        result = await chain.ainvoke(
            {
                "input": payload.message,
                "knowledge_context": self._build_context_text(retrieval.chunks),
            }
        )
        answer = self._extract_text(result)
        self._store_turn(
            payload.session_id,
            payload.message,
            answer,
            sources=self._serialize_sources(retrieval.sources),
            confidence_hint=retrieval.confidence_hint,
        )

        return ChatResponse(
            answer=answer,
            session_id=payload.session_id,
            used_demo_mode=False,
            sources=[
                ChatSource.model_validate(source.__dict__)
                for source in retrieval.sources
            ],
            confidence_hint=retrieval.confidence_hint,
        )

    def get_session_history(self, session_id: str) -> SessionHistoryResponse:
        settings = get_settings()
        rows = self.repository.get_session_messages(
            session_id=session_id,
            limit=settings.max_chat_history * 10,
        )
        return SessionHistoryResponse(
            session_id=session_id,
            messages=[
                HistoryMessage(
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                    sources=self._normalize_sources(row.get("sources")),
                    confidence_hint=row.get("confidence_hint"),
                )
                for row in rows
            ],
        )

    def get_system_status(self) -> dict[str, str | bool]:
        return database.get_status()

    def _get_history_messages(self, session_id: str) -> list[BaseMessage]:
        settings = get_settings()
        rows = self.repository.get_session_messages(
            session_id=session_id,
            limit=settings.max_chat_history * 2,
        )
        history: list[BaseMessage] = []
        for row in rows:
            if row["role"] == "human":
                history.append(HumanMessage(content=row["content"]))
            elif row["role"] == "ai":
                history.append(AIMessage(content=row["content"]))
        return history

    def _history_as_tuples(
        self,
        history: list[BaseMessage],
    ) -> list[tuple[str, str]]:
        messages: list[tuple[str, str]] = []
        for item in history:
            role = "human" if isinstance(item, HumanMessage) else "ai"
            messages.append((role, self._extract_text(item)))
        return messages

    def _extract_text(self, message: BaseMessage) -> str:
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _build_context_text(self, chunks: list[object]) -> str:
        if not chunks:
            return "Nenhum contexto confiavel foi encontrado."
        return "\n\n".join(
            f"Fonte: {chunk.filename}#chunk-{chunk.chunk_index}\nTrecho: {chunk.content}"
            for chunk in chunks
        )

    def _normalize_sources(self, raw_sources: object) -> list[ChatSource]:
        if not isinstance(raw_sources, list):
            return []

        sources: list[ChatSource] = []
        for item in raw_sources:
            if isinstance(item, dict):
                sources.append(ChatSource.model_validate(item))
                continue
            if isinstance(item, str):
                filename, chunk_index = self._parse_legacy_source(item)
                sources.append(
                    ChatSource(
                        filename=filename,
                        source_label=item,
                        chunk_index=chunk_index,
                    )
                )
        return sources

    def _parse_legacy_source(self, value: str) -> tuple[str, int | None]:
        if "#chunk-" not in value:
            return value, None
        filename, chunk_suffix = value.rsplit("#chunk-", maxsplit=1)
        try:
            return filename, int(chunk_suffix)
        except ValueError:
            return filename, None

    def _serialize_sources(
        self,
        sources: list[object],
    ) -> list[dict[str, object]]:
        serialized: list[dict[str, object]] = []
        for source in sources:
            if hasattr(source, "__dict__"):
                serialized.append(dict(source.__dict__))
        return serialized

    def _build_demo_answer(self, message: str) -> str:
        return (
            "Modo demo ativo. O fluxo FastAPI + LangChain + PostgreSQL esta preparado, "
            "mas a busca vetorial exige uma chave OpenAI valida.\n\n"
            f"Pergunta recebida: {message}\n\n"
            "Configure `OPENAI_API_KEY` para gerar embeddings, indexar documentos e consultar fontes reais."
        )

    def _store_turn(
        self,
        session_id: str,
        user_message: str,
        answer: str,
        *,
        sources: list[dict[str, object]],
        confidence_hint: str,
    ) -> None:
        self.repository.save_message(session_id, "human", user_message)
        self.repository.save_message(
            session_id,
            "ai",
            answer,
            sources=sources,
            confidence_hint=confidence_hint,
        )


assistant_service = AssistantService()
