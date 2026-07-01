"""Business logic for registration and login.

Routers stay thin (parse request, call service, return response); this
is where the actual rules live -- "email must be unique", "role is
always USER on self-registration", "don't leak which part of a login
attempt was wrong". None of that belongs in a route handler or in the
repository.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session) -> None:
        self._users = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        """Create a new user account.

        Role is hardcoded to USER here, not read from `payload` --
        `UserCreate` intentionally has no `role` field, but even if a
        client smuggled one in, this is the enforcement point that
        ignores it. Public registration can never create an admin.
        """
        if self._users.email_exists(payload.email):
            # 409 Conflict, not 400 -- the request is well-formed, it
            # just conflicts with existing state.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        return self._users.create(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRole.USER,
        )

    def authenticate(self, *, email: str, password: str) -> User:
        """Verify credentials and return the matching user.

        The error message is identical whether the email doesn't exist
        or the password is wrong -- distinguishing them would let an
        attacker use the login endpoint to enumerate registered email
        addresses one guess at a time.
        """
        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def create_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id))