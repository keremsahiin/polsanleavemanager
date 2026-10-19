"""Liveness and readiness signals (spec 0001 R-4..R-6): no session needed, no internals revealed."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import SQLAlchemyError

from app.platform.errors import not_ready
from app.platform.http import problem_response
from app.platform.schema import current_revisions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health")


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request) -> Response:
    state = request.app.state
    try:
        is_ready = current_revisions(state.engine) == state.latest_revisions
    except SQLAlchemyError, OSError:
        # The reason goes to the log only; the response must not reveal paths or error text.
        logger.warning("readiness check could not read the database", exc_info=True)
        is_ready = False
    if is_ready:
        return JSONResponse({"status": "ready"})
    return problem_response(not_ready())
