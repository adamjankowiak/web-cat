from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from cat_api.api.routes import demo, documents, glossary, segments, spellcheck, translation_memory
from cat_api.core.config import get_settings
from cat_api.schemas.health import HealthResponse


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared body exceeds ``max_bytes`` with HTTP 413.

    Import endpoints accept whole TXT/CSV/XML payloads as in-memory strings, so an
    unbounded body would let a single request exhaust server memory. Checking the
    Content-Length header rejects oversized uploads before they are read.
    """

    def __init__(self, app: object, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = None

            if declared_size is not None and declared_size > self.max_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"detail": "Request body is too large."},
                )

        return await call_next(request)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.max_request_body_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def healthcheck() -> HealthResponse:
        return HealthResponse(status="ok", service="cat-api", version=settings.app_version)

    app.include_router(documents.router)
    app.include_router(demo.router)
    app.include_router(segments.router)
    app.include_router(glossary.router)
    app.include_router(spellcheck.router)
    app.include_router(translation_memory.router)

    return app


app = create_app()
