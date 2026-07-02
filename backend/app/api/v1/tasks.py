"""Task endpoints: CRUD plus paginated, filterable, searchable, sortable
listing. Ownership rules (users see only their own tasks; admins see
everything) are enforced in TaskService, not here -- this file only
parses requests, delegates, and shapes responses.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.repositories.task_repository import SortField, SortOrder
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.task import PaginationMeta, TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

settings = get_settings()

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=SuccessResponse[TaskRead],
    status_code=201,
    summary="Create a task",
    description="The authenticated user becomes the task's owner. Every new task starts as TODO.",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskService(db).create_task(payload, current_user)
    return SuccessResponse(message="Task created successfully.", data=TaskRead.model_validate(task))


@router.get(
    "",
    response_model=PaginatedResponse[TaskRead],
    summary="List tasks (paginated, filterable, searchable, sortable)",
    description=(
        "Regular users see only their own tasks. Admins see all tasks. "
        "Supports filtering by status/priority, free-text search across "
        "title and description, and sorting by any whitelisted field."
    ),
)
def list_tasks(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    limit: int = Query(
        settings.default_page_size, ge=1, le=settings.max_page_size, description="Items per page"
    ),
    status_filter: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=200, description="Searches title and description"),
    sort_by: SortField = Query("created_at"),
    sort_order: SortOrder = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[TaskRead]:
    items, total = TaskService(db).list_tasks(
        current_user,
        status=status_filter,
        priority=priority,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    total_pages = math.ceil(total / limit) if limit else 0
    return PaginatedResponse(
        message="Tasks retrieved.",
        data=[TaskRead.model_validate(t) for t in items],
        meta=PaginationMeta(page=page, limit=limit, total_items=total, total_pages=total_pages),
    )


@router.get(
    "/{task_id}",
    response_model=SuccessResponse[TaskRead],
    summary="Get a single task by id",
    description="Returns 404 for tasks that don't exist AND for tasks that exist but belong to someone else.",
)
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskService(db).get_task(task_id, current_user)
    return SuccessResponse(message="Task retrieved.", data=TaskRead.model_validate(task))


@router.patch(
    "/{task_id}",
    response_model=SuccessResponse[TaskRead],
    summary="Partially update a task",
    description="Only fields included in the request body are changed. Owner or admin only.",
)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskService(db).update_task(task_id, payload, current_user)
    return SuccessResponse(message="Task updated successfully.", data=TaskRead.model_validate(task))


@router.delete(
    "/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Owner or admin only. Returns 204 No Content on success, per HTTP semantics for DELETE.",
)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    TaskService(db).delete_task(task_id, current_user)
    return Response(status_code=204)