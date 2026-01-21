"""
A thread pool backend for Django 6 tasks.

This backend executes tasks in a ThreadPoolExecutor, providing background
execution without external infrastructure. Suitable for development and
low-volume production use cases.

Usage in settings:
    TASKS = {
        "default": {
            "BACKEND": "tasks_threadpool.ThreadPoolBackend",
            "OPTIONS": {
                "MAX_WORKERS": 10,    # Thread pool size
                "MAX_RESULTS": 1000,  # Result retention limit
            }
        }
    }
"""

import logging
import traceback
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from django.tasks import TaskResult, TaskResultStatus
from django.tasks.backends.base import BaseTaskBackend
from django.tasks.base import Task, TaskError
from django.tasks.exceptions import TaskResultDoesNotExist

logger = logging.getLogger(__name__)

# Context variable for tasks to access their own result ID
current_result_id: ContextVar[str] = ContextVar("current_result_id")


@dataclass
class _BackendState:
    """Shared state for a ThreadPoolBackend instance."""

    executor: ThreadPoolExecutor
    results: dict[str, TaskResult]
    completed_ids: deque[str]
    lock: Lock
    max_results: int


# Module-level registry of backend state, keyed by alias.
# This ensures all backend instances for the same alias share state,
# even when Django creates separate instances per thread.
_backend_states: dict[str, _BackendState] = {}
_registry_lock = Lock()


class ThreadPoolBackend(BaseTaskBackend):
    """
    A Django Tasks backend that executes tasks in a thread pool.

    Simple, no infrastructure required - just threads.
    """

    # Backend capability flags - Django uses these to determine what features are available
    supports_defer = False  # No scheduled/delayed task execution
    supports_async_task = False  # No native async support (threads are synchronous)
    supports_get_result = True  # Results can be retrieved by ID

    def __init__(self, alias: str, params: dict[str, Any]) -> None:
        """
        Initialize the thread pool backend.

        Args:
            alias: The name of this backend in TASKS settings (e.g., "default")
            params: Configuration dict from TASKS settings, may contain OPTIONS
        """
        super().__init__(alias, params)
        options = params.get("OPTIONS", {})
        max_workers = options.get("MAX_WORKERS", 10)
        max_results = options.get("MAX_RESULTS", 1000)

        # Get or create shared state for this alias
        with _registry_lock:
            if alias not in _backend_states:
                _backend_states[alias] = _BackendState(
                    executor=ThreadPoolExecutor(max_workers=max_workers),
                    results={},
                    completed_ids=deque(),
                    lock=Lock(),
                    max_results=max_results,
                )
                logger.debug(
                    "ThreadPoolBackend '%s' initialized: max_workers=%d, max_results=%d, executor=%s",
                    alias,
                    max_workers,
                    max_results,
                    id(_backend_states[alias].executor),
                )

        self._state = _backend_states[alias]

    def _update_result(
        self,
        result_id: str,
        status: TaskResultStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        errors: list[TaskError] | None = None,
        return_value: Any = None,
        completed: bool = False,
    ) -> TaskResult | None:
        """
        Update a result's status in the store. Handles locking internally.

        Returns the updated result, or None if the result doesn't exist.
        """
        state = self._state
        with state.lock:
            if result_id not in state.results:
                return None
            old = state.results[result_id]
            result = TaskResult(
                id=old.id,
                task=old.task,
                status=status,
                enqueued_at=old.enqueued_at,
                started_at=started_at if started_at is not None else old.started_at,
                finished_at=finished_at,
                last_attempted_at=started_at
                if started_at is not None
                else old.last_attempted_at,
                args=old.args,
                kwargs=old.kwargs,
                backend=old.backend,
                errors=errors if errors is not None else old.errors,
                worker_ids=old.worker_ids,
            )
            if return_value is not None:
                # TaskResult is frozen, use object.__setattr__ to set _return_value
                object.__setattr__(result, "_return_value", return_value)
            state.results[result_id] = result
            if completed:
                state.completed_ids.append(result_id)
                self._evict_oldest()
            return result

    def _execute_task(self, result_id: str, task: Task) -> None:
        """
        Execute task in a worker thread and update the result store.

        This runs in a background thread, not the main request thread.
        """
        # Set context var so the task can access its own result ID if needed
        current_result_id.set(result_id)

        started_at = datetime.now(timezone.utc)

        # Update status to RUNNING now that we're actually executing
        result = self._update_result(result_id, TaskResultStatus.RUNNING, started_at)
        if result is None:
            return  # Task was removed, nothing to do

        try:
            return_value = task.func(*result.args, **result.kwargs)
            self._update_result(
                result_id,
                TaskResultStatus.SUCCESSFUL,
                finished_at=datetime.now(timezone.utc),
                return_value=return_value,
                completed=True,
            )
        except Exception as e:
            logger.exception("Task %s failed: %s", task.name, e)
            error = TaskError(
                exception_class_path=f"{type(e).__module__}.{type(e).__qualname__}",
                traceback=traceback.format_exc(),
            )
            self._update_result(
                result_id,
                TaskResultStatus.FAILED,
                finished_at=datetime.now(timezone.utc),
                errors=[error],
                completed=True,
            )

    def _evict_oldest(self) -> None:
        """Remove oldest completed results if over limit. Must hold state.lock."""
        state = self._state
        while len(state.completed_ids) > state.max_results:
            old_id = state.completed_ids.popleft()
            state.results.pop(old_id, None)

    def enqueue(
        self,
        task: Task,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> TaskResult:
        """
        Enqueue a task for background execution in the thread pool.

        Returns a TaskResult with the current status - READY if queued, RUNNING
        if a worker has already started, or even SUCCESSFUL for fast tasks.
        """
        self.validate_task(task)  # Raises if task is misconfigured

        now = datetime.now(timezone.utc)
        result = TaskResult(
            id=str(uuid.uuid4()),
            task=task,
            status=TaskResultStatus.READY,  # Always READY until worker starts
            enqueued_at=now,
            started_at=None,
            finished_at=None,
            last_attempted_at=None,
            args=list(args or ()),
            kwargs=dict(kwargs or {}),
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )

        state = self._state
        with state.lock:
            state.results[result.id] = result

        # Submit to thread pool - worker may start immediately
        state.executor.submit(self._execute_task, result.id, task)
        logger.debug(
            "Task '%s' enqueued: result_id=%s, executor=%s",
            task.name,
            result.id,
            id(state.executor),
        )

        # Return latest status (may have changed to RUNNING if worker started)
        with state.lock:
            return state.results.get(result.id, result)

    def get_result(self, result_id: str) -> TaskResult:
        """Retrieve a task result by ID."""
        state = self._state
        with state.lock:
            if result_id not in state.results:
                raise TaskResultDoesNotExist(result_id)
            return state.results[result_id]

    def close(self) -> None:
        """Shut down the thread pool. Cancels queued tasks, waits for running ones."""
        self._state.executor.shutdown(wait=True, cancel_futures=True)
