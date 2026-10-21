"""Composition root: assembles the FastAPI application (docs/architecture.md)."""

import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.platform import health, http
from app.platform.db import create_app_engine
from app.platform.schema import latest_revisions
from app.platform.settings import Settings

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Windows reads these from the registry, where .js is sometimes text/plain; with nosniff a browser
# would then refuse to run the page's module script.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")


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
    http.install(app)
    app.include_router(health.router)

    # Assets live under /static: a mount at "/" would claim every path, so a wrong method on an API
    # route would get the static handler's 405 (without Allow) instead of the router's.
    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
