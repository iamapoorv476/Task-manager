"""Authentication endpoints: registration and login.

Handlers here do three things and nothing else: parse the request
(FastAPI does this via the type hints), delegate to the service, and
shape the response. No password hashing, no token creation, no DB
queries happen directly in this file.
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
    summary="Register a new user account",
    description=(
        "Creates a new user with the USER role. Role cannot be set by the "
        "client -- admin accounts are never created via public registration."
    ),
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user = AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and obtain a JWT access token",
    description=(
        "Accepts standard OAuth2 password-flow form fields: `username` "
        "(use your email address here) and `password`. This form-based "
        "shape -- rather than a JSON body -- is what allows Swagger's "
        "'Authorize' button to work directly against this endpoint."
    ),
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    service = AuthService(db)
    user = service.authenticate(email=form_data.username, password=form_data.password)
    token = service.create_token(user)
    return Token(access_token=token, token_type="bearer")