"""Shared FastAPI dependencies for authentication and authorization.

Every protected route depends on `get_current_user` (or `require_admin`,
which builds on it) rather than duplicating JWT-decoding logic in each
router. This is the single choke point where "is this request allowed
to proceed" is decided.
"""

import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

settings = get_settings()

# tokenUrl only affects the Swagger "Authorize" button (it needs to know
# where to POST credentials for the interactive docs) -- it plays no role
# in actual token verification. Note: if the request has NO Authorization
# header at all, OAuth2PasswordBearer raises its own HTTPException(401)
# here, before get_current_user's body ever runs -- that case is handled
# separately by the Starlette HTTPException handler in
# core/exception_handlers.py, not by UnauthorizedException below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated User from a bearer JWT.

    Deliberately re-fetches the user from the database on every request
    rather than trusting claims embedded in the token itself. The token
    only proves *identity* (who successfully logged in and when); the
    database is the source of truth for whether that user still exists
    and what role they currently hold. This means a deleted account or a
    role change takes effect on the very next request, instead of only
    after the token naturally expires (up to `access_token_expire_minutes`
    later). The cost is one indexed primary-key lookup per authenticated
    request -- cheap, and a reasonable trade for that correctness
    guarantee at this scale.
    """
    try:
        payload = decode_access_token(token)
        raw_user_id = payload.get("sub")
        if raw_user_id is None:
            raise UnauthorizedException
        user_id = uuid.UUID(raw_user_id)
    except (JWTError, ValueError) as exc:
        raise UnauthorizedException from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedException
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Authorization guard: only proceeds if the current user is an ADMIN.

    Composed on top of `get_current_user` rather than duplicating token
    logic -- authentication and authorization are separate concerns
    (who are you vs. what are you allowed to do), and this keeps that
    boundary explicit in the dependency graph itself.
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("This action requires administrator privileges.")
    return current_user