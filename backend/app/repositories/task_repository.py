"""Data-access layer for the Task entity.

Contains ONLY query construction -- ownership rules, "who's allowed to
see this" decisions, and any other business logic live in TaskService,
not here. This repository doesn't know what a "user" is allowed to do;
it just knows how to fetch, filter, sort, and paginate tasks given
whatever constraints the service passes in.
"""

import uuid
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus

# Whitelisted sortable columns. A client-supplied string is NEVER passed
# directly into getattr()/order_by() -- only keys from this dict are
# reachable, so there's no path from user input to an arbitrary column
# or SQL injection via the sort parameter.
_SORTABLE_COLUMNS = {
    "created_at": Task.created_at,
    "updated_at": Task.updated_at,
    "title": Task.title,
    "priority": Task.priority,
    "status": Task.status,
}

SortField = Literal["created_at", "updated_at", "title", "priority", "status"]
SortOrder = Literal["asc", "desc"]


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        return self._db.get(Task, task_id)

    def create(
        self,
        *,
        title: str,
        description: str | None,
        priority: TaskPriority,
        owner_id: uuid.UUID,
    ) -> Task:
        task = Task(title=title, description=description, priority=priority, owner_id=owner_id)
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def update(self, task: Task, **fields: object) -> Task:
        for key, value in fields.items():
            setattr(task, key, value)
        self._db.commit()
        self._db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        self._db.delete(task)
        self._db.commit()

    def list(
        self,
        *,
        owner_id: uuid.UUID | None,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        search: str | None,
        sort_by: SortField,
        sort_order: SortOrder,
        skip: int,
        limit: int,
    ) -> tuple[list[Task], int]:
        """Returns (page_of_tasks, total_matching_count).

        `owner_id=None` means "no owner filter" -- i.e. an admin listing
        all tasks. The caller (TaskService) is responsible for deciding
        when that's appropriate; this method just applies whatever
        filter it's given.
        """
        stmt = select(Task)

        if owner_id is not None:
            stmt = stmt.where(Task.owner_id == owner_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                (Task.title.ilike(pattern)) | (Task.description.ilike(pattern))
            )

        # Count total matches BEFORE applying pagination, so the client
        # gets an accurate total_pages/total_items regardless of which
        # page they requested.
        total = self._db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        column = _SORTABLE_COLUMNS[sort_by]
        order_clause = column.asc() if sort_order == "asc" else column.desc()
        stmt = stmt.order_by(order_clause).offset(skip).limit(limit)

        items = list(self._db.scalars(stmt))
        return items, total