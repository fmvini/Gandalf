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
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.rate_limit import RateLimiter
from app.database.session import make_engine
from app.providers.base import BookProvider
from app.providers.local_catalog import LocalBookProvider
from app.providers.open_library import OpenLibraryProvider
from app.routes.auth import router as auth_router
from app.routes.books import router as books_router
from app.routes.recommendations import router as recommendations_router
from app.services.book_service import BookService
from app.services.recommendation_service import RANKING_VERSION, RecommendationService

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
            engine = make_engine(config.database_url) if config.database_url else None
            application.state.engine = engine
            application.state.session_factory = (
                sessionmaker(engine, expire_on_commit=False, class_=Session)
                if engine is not None
                else None
            )
            provider = book_provider
            if provider is None and config.book_provider == "local":
                provider = LocalBookProvider()
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
                provider,
                config.book_search_cache_ttl_seconds,
                application.state.session_factory,
            )
            application.state.recommendation_service = RecommendationService()
            try:
                yield
            finally:
                if engine is not None:
                    engine.dispose()

    application = FastAPI(
        title=config.app_name, version=config.app_version, lifespan=lifespan
    )
    application.state.settings = config
    application.state.auth_limiter = RateLimiter(config.auth_rate_limit_per_minute)
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
    def readiness() -> JSONResponse:
        engine = application.state.engine
        components = {"database": "down", "schema": "down", "pgvector": "down"}
        if engine is not None:
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                    components["database"] = "ok"
                    from app.database.base import Base

                    if set(Base.metadata.tables) <= set(
                        inspect(connection).get_table_names()
                    ):
                        components["schema"] = "ok"
                    if connection.dialect.name == "sqlite":
                        components["pgvector"] = "not_required"
                    if connection.dialect.name == "postgresql":
                        has_vector = connection.scalar(
                            text(
                                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                            )
                        )
                        if has_vector:
                            components["pgvector"] = "ok"
            except SQLAlchemyError:
                pass
        ready = all(status in {"ok", "not_required"} for status in components.values())
        return JSONResponse(
            status_code=200 if ready else 503,
            content={"status": "ok" if ready else "down", "components": components},
        )

    @application.get("/version", tags=["health"])
    async def version() -> dict[str, str | None]:
        return {
            "app": config.app_name,
            "version": config.app_version,
            "ranking_version": RANKING_VERSION,
        }

    application.include_router(books_router)
    application.include_router(auth_router)
    application.include_router(recommendations_router)
    return application


app = create_app()
