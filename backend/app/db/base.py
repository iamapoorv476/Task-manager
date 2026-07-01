"""SQLAlchemy declarative base.

Kept in its own module (rather than alongside session setup) so that models
can import `Base` without triggering engine/session creation, and so Alembic
can import it without pulling in the full app.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
