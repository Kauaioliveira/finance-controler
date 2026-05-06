from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.assistant import assistant_service


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    assistant_service.initialize()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.2.0",
    description=(
        "API base para um assistente contabil usando FastAPI e LangChain."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def _error_payload(
    *,
    detail: str,
    code: str,
    field_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "detail": detail,
        "code": code,
    }
    if field_errors:
        payload["field_errors"] = field_errors
    return payload


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            detail=exc.detail,
            code=exc.code,
            field_errors=exc.field_errors,
        ),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            detail="Erro de validacao na requisicao.",
            code="request_validation_error",
            field_errors=[
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ],
        ),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if settings.app_debug:
        detail = str(exc) or "Erro interno nao tratado."
    else:
        detail = "Erro interno nao tratado."
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            detail=detail,
            code="internal_error",
        ),
    )


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "message": "Assistente contabil online.",
        "docs": "/docs",
    }


