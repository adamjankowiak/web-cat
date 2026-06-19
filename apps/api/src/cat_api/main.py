from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cat_api.api.routes import demo, documents, glossary, segments, spellcheck, translation_memory
from cat_api.core.config import get_settings
from cat_api.schemas.health import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

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
