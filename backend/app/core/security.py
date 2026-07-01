"""Password hashing and JWT token utilities.

Isolated here -- rather than scattered across services -- so there is
exactly one place in the codebase that knows about bcrypt and JWT
internals. Services call these functions without needing to know how a
token is signed or how a password is hashed; if we ever rotate the
hashing algorithm or JWT library, this is the only file that changes.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# bcrypt is deliberately the only scheme. `deprecated="auto"` means if we
# ever add a stronger scheme (e.g. argon2) to this list, passlib will
# transparently re-hash existing users' passwords on their next successful
# login -- no bulk data migration required.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store plaintext passwords."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    `subject` is the user's id (as a string) and becomes the JWT `sub`
    claim. Deliberately minimal payload -- we do NOT embed role or other
    mutable user attributes in the token. Embedding them would mean a
    revoked user or a role change (e.g. USER -> ADMIN, or vice versa)
    wouldn't take effect until the token naturally expires. Instead the
    token only proves *identity*; `get_current_user` re-fetches the user
    from the DB on every request to get their *current* role and
    confirm they still exist. See api/deps.py for that tradeoff in
    detail.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, Any] = {"sub": subject, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Raises `jose.JWTError` if the token is malformed, has an invalid
    signature, or has expired. Callers (see api/deps.py) are responsible
    for translating that into an HTTP 401.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])