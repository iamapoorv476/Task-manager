"""Domain-level exceptions.

Services raise these instead of framework `HTTPException`s. Each carries
its own HTTP status code, but the exception itself is otherwise just a
plain Python exception -- it doesn't know anything about how it will be
serialized. That translation happens once, centrally, in
`exception_handlers.py`. The benefit: business logic reads as business
logic ("user not found", "email already exists"), not as a mix of
business logic and HTTP-response construction.
"""


class AppException(Exception):
    """Base class for all domain-level exceptions."""

    status_code: int = 500
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundException(AppException):
    status_code = 404
    default_message = "The requested resource was not found."


class ConflictException(AppException):
    status_code = 409
    default_message = "The request conflicts with the current state of the resource."


class UnauthorizedException(AppException):
    status_code = 401
    default_message = "Could not validate credentials."


class ForbiddenException(AppException):
    status_code = 403
    default_message = "You do not have permission to perform this action."


class BadRequestException(AppException):
    status_code = 400
    default_message = "The request could not be processed."