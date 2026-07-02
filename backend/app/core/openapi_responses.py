"""Reusable OpenAPI response documentation.

FastAPI only documents a route's error responses if you tell it to --
by default Swagger only shows the success path. Since every error this
API returns follows the same envelope (see core/exception_handlers.py),
I only need to describe each status code once here and reuse it, rather
than repeating the same block on every route in every router.
"""

from app.schemas.common import ErrorResponse

UNAUTHORIZED = {
    401: {
        "model": ErrorResponse,
        "description": "Missing, invalid, or expired authentication token.",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "Could not validate credentials",
                    "errors": [],
                }
            }
        },
    }
}

FORBIDDEN = {
    403: {
        "model": ErrorResponse,
        "description": "Authenticated, but the account doesn't have the required role.",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "This action requires administrator privileges.",
                    "errors": [],
                }
            }
        },
    }
}

NOT_FOUND = {
    404: {
        "model": ErrorResponse,
        "description": (
            "The resource doesn't exist, or it exists but belongs to a different "
            "user (both cases return 404, on purpose -- see the ownership note above)."
        ),
        "content": {
            "application/json": {
                "example": {"success": False, "message": "Task not found.", "errors": []}
            }
        },
    }
}

CONFLICT = {
    409: {
        "model": ErrorResponse,
        "description": "The request conflicts with existing state (e.g. email already registered).",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "A user with this email already exists.",
                    "errors": [],
                }
            }
        },
    }
}

VALIDATION_ERROR = {
    422: {
        "model": ErrorResponse,
        "description": "Request body or query parameters failed validation.",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": ["password: password must be at least 8 characters long"],
                }
            }
        },
    }
}