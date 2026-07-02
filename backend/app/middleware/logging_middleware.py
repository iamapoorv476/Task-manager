"""Request logging middleware.

Logs exactly one line per request: method, path, status code, how long
it took, a request ID for correlating with anything else that happened
during that request, and the authenticated user's id if there was one.
That's the full list the assignment asked for, and it's genuinely the
set of fields I'd want in front of me first when debugging a production
issue at 2am.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.user_id = None  # get_current_user overwrites this if the request is authenticated

        # Bound via contextvars so anything logged DURING route handling
        # (including the exception handler's logging.getLogger("app")
        # calls) automatically picks up request_id without having to
        # pass it around explicitly.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                # Read from request.state, not contextvars -- see the
                # module docstring in core/logging.py and the note in
                # api/deps.py for why user_id specifically needs this.
                user_id=request.state.user_id,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = logger.warning if response.status_code >= 500 else logger.info
        log(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=request.state.user_id,
        )

        response.headers["X-Request-ID"] = request_id
        return response