"""Data-access layer for the User entity.

Contains ONLY query construction -- no business logic, no password
hashing, no authorization decisions. Services depend on this class
rather than importing SQLAlchemy directly, which means:
  1. Business logic can be unit-tested against a fake/mock repository
     without spinning up a real database.
  2. Query logic for "how do we fetch a user" lives in exactly one
     place, so it can't drift between the auth service, the admin
     user-listing endpoint, and anywhere else that needs a user.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == email))

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        user = User(name=name, email=email, password_hash=password_hash, role=role)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def list_all(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        return list(self._db.scalars(stmt))

    def count(self) -> int:
        return self._db.scalar(select(func.count()).select_from(User)) or 0