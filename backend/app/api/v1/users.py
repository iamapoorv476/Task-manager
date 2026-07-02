"""User endpoints: self-profile and admin user listing."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.openapi_responses import FORBIDDEN, UNAUTHORIZED
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import SuccessResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=SuccessResponse[UserRead],
    summary="Get the current authenticated user's profile",
    responses={**UNAUTHORIZED},
)
def get_my_profile(current_user: User = Depends(get_current_user)) -> SuccessResponse[UserRead]:
    return SuccessResponse(message="Profile retrieved.", data=UserRead.model_validate(current_user))


@router.get(
    "",
    response_model=SuccessResponse[list[UserRead]],
    summary="List all users (admin only)",
    description="Requires the ADMIN role. A regular user gets 403, not an empty list.",
    responses={**UNAUTHORIZED, **FORBIDDEN},
)
def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip, for pagination."),
    limit: int = Query(50, ge=1, le=200, description="Max users to return."),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SuccessResponse[list[UserRead]]:
    users = UserRepository(db).list_all(skip=skip, limit=limit)
    return SuccessResponse(
        message="Users retrieved.", data=[UserRead.model_validate(u) for u in users]
    )