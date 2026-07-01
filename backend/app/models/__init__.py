"""Import all models here so Base.metadata is fully populated for Alembic
autogenerate and for `Base.metadata.create_all()` in tests."""

from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401
