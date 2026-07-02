"""Pydantic schemas for authentication responses."""

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZmE4NWY2NC01NzE3LTQ1NjItYjNmYy0yYzk2M2Y2NmFmYTYiLCJpYXQiOjE3MTk4MDAwMDAsImV4cCI6MTcxOTgwMzYwMH0.signature-truncated-for-readability",
                "token_type": "bearer",
            }
        }
    )

    access_token: str
    token_type: str = "bearer"