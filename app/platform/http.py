"""HTTP plumbing shared by every route (docs/conventions.md, Error handling; docs/security.md).

RequestContextMiddleware is the outermost layer we control. It also turns unexpected errors into
the 500 problem response: Starlette would otherwise build that response in ServerErrorMiddleware,
outside every user middleware, without security headers or correlation id (plan 0001, risk 2).
"""

import logging
import re
import time
import uuid
from collections.abc import Mapping
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.platform.errors import (
    PROBLEM_MEDIA_TYPE,
    DomainError,
    Problem,
    internal_error,
    method_not_allowed,
    not_found,
)

REQUEST_ID_HEADER = "x-request-id"
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9-]{1,64}")

SECURITY_HEADERS = {
    "content-security-policy": (
        "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
    "x-content-type-options": "nosniff",
    "referrer-policy": "same-origin",
}

request_logger = logging.getLogger("app.request")
error_logger = logging.getLogger("app.error")


def correlation_id_from(incoming: str | None) -> str:
    """Use a well-formed incoming request id (e.g. from the reverse proxy), else generate one."""
    if incoming is not None and _VALID_REQUEST_ID.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex


def problem_response(problem: Problem, headers: Mapping[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        problem.to_dict(),
        status_code=problem.status,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=headers,
    )


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        correlation_id = correlation_id_from(Headers(scope=scope).get(REQUEST_ID_HEADER))
        started = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_context(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
                headers[REQUEST_ID_HEADER] = correlation_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        except Exception:
            # The detail stays in the log, tied to the id the user sees (spec 0001 R-7, R-8).
            error_logger.exception(
                "unhandled error while serving a request", extra={"correlation_id": correlation_id}
            )
            status = 500
            if not response_started:
                await problem_response(internal_error(correlation_id))(
                    scope, receive, send_with_context
                )
        finally:
            # Path only: no query string, body, cookies or personal data (docs/security.md).
            request_logger.info(
                "request",
                extra={
                    "correlation_id": correlation_id,
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )


def _http_exception_handler(_request: Request, error: Exception) -> Response:
    exc = cast(StarletteHTTPException, error)  # registered for this type only (install below)
    if exc.status_code == 404:
        return problem_response(not_found())
    if exc.status_code == 405:
        return problem_response(method_not_allowed(), headers=exc.headers)
    return problem_response(
        Problem(
            status=exc.status_code,
            code=f"platform.http_{exc.status_code}",
            title="İstek işlenemedi",
            detail="İstek bu haliyle işlenemedi.",
        ),
        headers=exc.headers,
    )


def _domain_error_handler(_request: Request, error: Exception) -> Response:
    return problem_response(cast(DomainError, error).to_problem())


def install(app: FastAPI) -> None:
    """Attach the shared error handlers and the request middleware to an application."""
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(DomainError, _domain_error_handler)
    app.add_middleware(RequestContextMiddleware)
