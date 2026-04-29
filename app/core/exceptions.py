class AppError(Exception):
    status_code = 500
    detail = "Erro interno da aplicacao."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class ValidationError(AppError):
    status_code = 400
    detail = "Os dados enviados sao invalidos."


class NotFoundError(AppError):
    status_code = 404
    detail = "Recurso nao encontrado."


class InfrastructureError(AppError):
    status_code = 503
    detail = "Infraestrutura indisponivel no momento."


class DocumentProcessingError(AppError):
    status_code = 400
    detail = "Nao foi possivel processar o documento enviado."
