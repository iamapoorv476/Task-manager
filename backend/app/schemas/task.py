"""Pydantic schemas for the Task resource."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM

    @field_validator("title")
    @classmethod
    def title_must_be_meaningful(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("title must be at least 3 characters long")
        if len(v) > 200:
            raise ValueError("title must be at most 200 characters long")
        return v


class TaskCreate(TaskBase):
    """Note: no `status` field -- every task is created as TODO. Letting a
    client create a task as already DONE would be unusual and is easy to
    add later if a real requirement calls for it; starting restrictive is
    safer than starting permissive."""


class TaskUpdate(BaseModel):
    """All fields optional -- this backs PATCH (partial update), not PUT.
    Only fields the client actually sends get changed; everything else on
    the task is left untouched."""

    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None

    @field_validator("title")
    @classmethod
    def title_must_be_meaningful(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 3:
            raise ValueError("title must be at least 3 characters long")
        if len(v) > 200:
            raise ValueError("title must be at most 200 characters long")
        return v


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: TaskStatus
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    limit: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)