"""Business logic for task management.

Ownership enforcement lives here, in exactly one place (`_ensure_access`),
so get/update/delete can't drift out of sync with each other -- every
mutating or single-resource operation routes through the same check.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.task import Task
from app.models.user import User, UserRole
from app.repositories.task_repository import SortField, SortOrder, TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session) -> None:
        self._tasks = TaskRepository(db)

    def create_task(self, payload: TaskCreate, owner: User) -> Task:
        return self._tasks.create(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            owner_id=owner.id,
        )

    def get_task(self, task_id: uuid.UUID, current_user: User) -> Task:
        task = self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundException("Task not found.")
        self._ensure_access(task, current_user)
        return task

    def update_task(self, task_id: uuid.UUID, payload: TaskUpdate, current_user: User) -> Task:
        task = self.get_task(task_id, current_user)  # reuses ownership check
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return task
        return self._tasks.update(task, **changes)

    def delete_task(self, task_id: uuid.UUID, current_user: User) -> None:
        task = self.get_task(task_id, current_user)
        self._tasks.delete(task)

    def list_tasks(
        self,
        current_user: User,
        *,
        status=None,
        priority=None,
        search: str | None = None,
        sort_by: SortField = "created_at",
        sort_order: SortOrder = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[Task], int]:
        # Regular users are implicitly scoped to their own tasks; admins
        # get owner_id=None, meaning "no filter, show everything". This
        # is the one place list-scope-by-role is decided.
        owner_id = None if current_user.role == UserRole.ADMIN else current_user.id
        skip = (page - 1) * limit
        return self._tasks.list(
            owner_id=owner_id,
            status=status,
            priority=priority,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit,
        )

    def _ensure_access(self, task: Task, current_user: User) -> None:
        """Admins may access any task. Regular users may only access
        their own. A non-owned task raises NotFoundException (404), not
        a Forbidden (403) -- returning 403 would confirm the task exists
        under someone else's account, which is information a user who
        doesn't own it shouldn't be able to extract just by guessing IDs.
        """
        if current_user.role != UserRole.ADMIN and task.owner_id != current_user.id:
            raise NotFoundException("Task not found.")