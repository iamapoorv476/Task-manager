"""Centralized exception handlers.

Every error response leaving this API -- a caught domain exception, a
request that failed Pydantic validation, a framework-level error like
"no Authorization header", or a genuinely unexpected bug -- passes
through exactly one of these handlers and comes out in the same
{success, message, errors} shape. This is what lets frontend code
write ONE error-handling path instead of special-casing each endpoint's
failure response.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.schemas.common import ErrorResponse

logger = logging.getLogger("app")


def _error_response(
    status_code: int,
    message: str,
    errors: list[str] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(message=message, errors=errors or [])
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    # 401s need WWW-Authenticate per the OAuth2 spec, or some HTTP
    # clients / browsers won't correctly prompt for re-authentication.
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == status.HTTP_401_UNAUTHORIZED else None
    return _error_response(exc.status_code, exc.message, headers=headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Catches framework-raised HTTPExceptions our own code never touches --
    e.g. OAuth2PasswordBearer raising 401 when no Authorization header is
    present at all (that happens before our route/dependency code runs),
    or Starlette's own 404/405 for unmatched routes. Without this handler
    those would leak FastAPI's default {"detail": "..."} shape instead of
    our envelope.
    """
    headers = dict(exc.headers) if exc.headers else None
    return _error_response(exc.status_code, str(exc.detail), headers=headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        f"{'.'.join(str(loc) for loc in e['loc'] if loc != 'body')}: {e['msg']}" for e in exc.errors()
    ]
    return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation failed.", errors=errors)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Full exception logged server-side for debugging; client gets a
    # generic message only. Never expose internal exception details
    # (stack traces, DB error strings, file paths) to the client -- that
    # information is a reconnaissance gift to an attacker.
    logger.exception("Unhandled exception processing %s %s", request.method, request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "An internal server error occurred."
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)