"""Composition root: assembles the FastAPI application (docs/architecture.md)."""

from fastapi import FastAPI

from app.platform.settings import Settings


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Polsan İzin Yönetimi", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    return app
