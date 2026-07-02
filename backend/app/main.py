"""Application entrypoint.

Uses an app-factory function (`create_app`) rather than a bare module-level
`FastAPI()` instance. This matters for testing: pytest fixtures can call
`create_app()` fresh for isolated test runs and override dependencies
(e.g. swap `get_db` for a test-database session) without those overrides
leaking between tests via a shared global instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, tasks, users
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "I built this as a task management API to show how I structure a "
            "backend for production, not just to satisfy a checklist. Routers stay "
            "thin, business rules live in services, and data access is isolated in "
            "repositories -- so the auth logic, ownership rules, and query filtering "
            "can each be read (and tested) on their own.\n\n"
            "A few things worth knowing before you try the endpoints below:\n"
            "- Every response, success or error, comes back in the same "
            "`{success, message, data}` / `{success, message, errors}` shape.\n"
            "- Regular users only ever see their own tasks. Admins see everything. "
            "Trying to access someone else's task returns 404, not 403 -- "
            "I didn't want a non-owner to be able to tell a task exists just from "
            "the error code.\n"
            "- To try protected endpoints here: register, log in, then click "
            "**Authorize** above and paste the token you get back."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "Register and log in. Login returns the JWT you'll need for everything below.",
            },
            {
                "name": "Users",
                "description": "Your own profile, plus an admin-only endpoint to list every user.",
            },
            {
                "name": "Tasks",
                "description": (
                    "The actual product: create, read, update, delete, and search "
                    "tasks. Regular users are scoped to their own; admins can act "
                    "on anyone's."
                ),
            },
            {"name": "Health", "description": "Liveness check for load balancers and uptime monitors."},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(users.router, prefix=settings.api_v1_prefix)
    app.include_router(tasks.router, prefix=settings.api_v1_prefix)
    
    register_exception_handlers(app)

    @app.get("/health", tags=["Health"], summary="Liveness check")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()