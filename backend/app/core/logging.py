"""Structured logging configuration.

Wires structlog into Python's standard logging module so that both
`structlog.get_logger()` calls AND plain `logging.getLogger(name)` calls
(like the one already in core/exception_handlers.py) end up going
through the same processor pipeline and come out in the same shape.
I didn't want to have to remember which style of logger to use where --
this way it doesn't matter.

In development, logs render as colored, readable console output. In any
other environment (testing, production), they render as JSON -- one
object per line, which is what log aggregators (CloudWatch, Datadog,
whatever) expect.
"""

import logging
import sys

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()

    # These run on every log event, structlog or stdlib, before rendering.
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.environment == "development"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # foreign_pre_chain runs shared_processors on log records that came
    # from plain `logging.getLogger(...)` calls too, not just structlog
    # ones -- this is what makes core/exception_handlers.py's existing
    # `logging.getLogger("app")` calls come out with the same JSON shape
    # and the same request_id/user_id context, with zero changes needed
    # to that file.
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    # uvicorn's own access log duplicates what my request-logging
    # middleware already reports (and in a different, non-JSON format),
    # so I quiet it down to avoid every request being logged twice.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)