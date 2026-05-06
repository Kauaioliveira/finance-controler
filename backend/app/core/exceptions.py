class AppError(Exception):
    status_code = 500
    detail = "Erro interno da aplicacao."
    code = "internal_error"

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        field_errors: list[dict[str, object]] | None = None,
    ) -> None:
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail
        self.code = code or self.code
        self.field_errors = field_errors or []


class ValidationError(AppError):
    status_code = 400
    detail = "Os dados enviados sao invalidos."
    code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    detail = "Recurso nao encontrado."
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    detail = "Conflito de dados."
    code = "conflict"


class AuthenticationError(AppError):
    status_code = 401
    detail = "Autenticacao invalida."
    code = "authentication_error"


class AuthorizationError(AppError):
    status_code = 403
    detail = "Voce nao tem permissao para executar esta acao."
    code = "authorization_error"


class InfrastructureError(AppError):
    status_code = 503
    detail = "Infraestrutura indisponivel no momento."
    code = "infrastructure_error"


class DocumentProcessingError(AppError):
    status_code = 400
    detail = "Nao foi possivel processar o documento enviado."
    code = "document_processing_error"
