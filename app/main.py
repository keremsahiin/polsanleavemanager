"""Composition root: assembles the FastAPI application (docs/architecture.md)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.platform import health
from app.platform.db import create_app_engine
from app.platform.schema import latest_revisions
from app.platform.settings import Settings


def create_app(settings: Settings) -> FastAPI:
    # No connection is opened here: the app never creates or migrates the database (spec 0001 R-2).
    engine = create_app_engine(settings.database_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="Polsan İzin Yönetimi",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.latest_revisions = latest_revisions()
    app.include_router(health.router)
    return app
