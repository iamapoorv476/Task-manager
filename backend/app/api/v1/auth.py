"""Authentication endpoints: registration and login.

Handlers here do three things and nothing else: parse the request
(FastAPI does this via the type hints), delegate to the service, and
shape the response. No password hashing, no token creation, no DB
queries happen directly in this file.
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.openapi_responses import CONFLICT, VALIDATION_ERROR
from app.db.session import get_db
from app.schemas.auth import Token
from app.schemas.common import SuccessResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserRead],
    status_code=201,
    summary="Register a new user account",
    description=(
        "Creates a new user with the USER role. Role isn't a field you can set here "
        "-- admin accounts are never created through public registration, only by "
        "promoting an existing user directly."
    ),
    responses={**CONFLICT, **VALIDATION_ERROR},
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> SuccessResponse[UserRead]:
    user = AuthService(db).register(payload)
    return SuccessResponse(message="User registered successfully.", data=UserRead.model_validate(user))


@router.post(
    "/login",
    response_model=SuccessResponse[Token],
    summary="Log in and get a JWT access token",
    description=(
        "Uses the standard OAuth2 password flow, so the form fields are `username` "
        "and `password` -- put your email address in `username`. This is also what "
        "lets Swagger's Authorize button work directly against this endpoint, "
        "instead of needing a separate JSON login form."
    ),
    responses={
        401: {
            "description": "Wrong email or password. Same message either way, so a "
            "failed login can't be used to check which emails are registered.",
        }
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> SuccessResponse[Token]:
    service = AuthService(db)
    user = service.authenticate(email=form_data.username, password=form_data.password)
    token = service.create_token(user)
    return SuccessResponse(
        message="Login successful.", data=Token(access_token=token, token_type="bearer")
    )