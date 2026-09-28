import json
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from time import perf_counter
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings
from app.core.exceptions import AppError
from app.providers.base import BookProvider
from app.providers.open_library import OpenLibraryProvider
from app.routes.books import router as books_router
from app.services.book_service import BookService

logger = logging.getLogger("gandalf.api")


def error_response(
    request: Request, status_code: int, code: str, message: str, **extra: object
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                **extra,
                "request_id": request.state.request_id,
            }
        },
    )


def create_app(
    *, settings: Settings | None = None, book_provider: BookProvider | None = None
) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with AsyncExitStack() as stack:
            provider = book_provider
            if provider is None:
                client = await stack.enter_async_context(
                    httpx.AsyncClient(timeout=httpx.Timeout(5.0))
                )
                provider = OpenLibraryProvider(
                    client,
                    base_url=config.open_library_base_url,
                    contact_email=config.open_library_contact_email,
                )
            application.state.book_service = BookService(
                provider, config.book_search_cache_ttl_seconds
            )
            yield

    application = FastAPI(
        title=config.app_name, version=config.app_version, lifespan=lifespan
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        supplied_id = request.headers.get("X-Request-ID", "")
        try:
            request_id = str(UUID(supplied_id))
        except (ValueError, AttributeError):
            request_id = str(uuid4())
        request.state.request_id = request_id
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                }
            )
        )
        return response

    @application.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        response = error_response(request, exc.status_code, exc.code, exc.message)
        if exc.retry_after is not None:
            response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"][1:]),
                "issue": error["type"],
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return error_response(
            request,
            422,
            "VALIDATION_ERROR",
            "Confira os dados enviados.",
            details=details,
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "BAD_REQUEST"
        message = (
            "Recurso não encontrado."
            if exc.status_code == 404
            else "Requisição inválida."
        )
        return error_response(request, exc.status_code, code, message)

    @application.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected API error", exc_info=exc)
        return error_response(
            request, 500, "INTERNAL_ERROR", "Ocorreu um erro inesperado."
        )

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready", tags=["health"])
    async def readiness() -> JSONResponse:
        # Ainda não há banco configurado: a aplicação não está pronta para o MVP completo.
        return JSONResponse(
            status_code=503,
            content={"status": "down", "components": {"database": "down"}},
        )

    @application.get("/version", tags=["health"])
    async def version() -> dict[str, str | None]:
        return {
            "app": config.app_name,
            "version": config.app_version,
            "ranking_version": None,
        }

    application.include_router(books_router)
    return application


app = create_app()
