"""Database engine and session management.

Provides a single engine per process and a request-scoped session via the
`get_db` FastAPI dependency, which guarantees sessions are always closed
(and rolled back on error) even if a request handler raises.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping avoids serving stale connections after DB restarts/idle
# timeouts -- a common source of intermittent 500s in production without it.
engine = create_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped DB session.

    The try/finally guarantees the session (and its connection) is always
    returned to the pool, regardless of whether the request succeeded,
    raised a handled AppException, or raised an unexpected exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
