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


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "A production-oriented Task Management REST API demonstrating "
            "JWT authentication, role-based access control, and clean "
            "layered architecture (router -> service -> repository)."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Restricted to configured origins (not "*") because credentialed
    # requests (cookies/Authorization headers) combined with a wildcard
    # origin is a CORS misconfiguration browsers increasingly reject
    # outright, and is a real cross-origin data-leak risk when they don't.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(users.router, prefix=settings.api_v1_prefix)
    app.include_router(tasks.router, prefix=settings.api_v1_prefix)
    
    register_exception_handlers(app)

    @app.get("/health", tags=["Health"], summary="Liveness check")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()