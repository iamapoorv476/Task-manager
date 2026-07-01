"""Common response envelope schemas.

Every successful response is {success: true, message, data}; every error
response is {success: false, message, errors}. Using Pydantic generics
for SuccessResponse (rather than returning a bare dict) means Swagger
documents the *actual* shape of `data` for each endpoint -- e.g.
SuccessResponse[UserRead] shows a real UserRead schema nested inside,
not an opaque "object".
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[str] = []