"""Shared executor state registry for backend instances."""

from collections import deque
from concurrent.futures import Executor, Future
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class ExecutorState:
    """Shared state for all backend instances using the same executor.

    Multiple backend instances with the same name share:
    - The executor (thread/process pool)
    - The futures dict (in-flight tasks)
    - The results dict (completed tasks)
    """

    executor: Executor
    futures: dict[str, Future] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    completed_ids: deque[str] = field(default_factory=deque)
    max_results: int = 1000
    lock: Lock = field(default_factory=Lock)


_executor_states: dict[str, ExecutorState] = {}
_registry_lock = Lock()


def get_executor_state(
    name: str,
    executor_class: type[Executor],
    max_workers: int,
    max_results: int,
) -> ExecutorState:
    """Get or create shared executor state by name.

    Args:
        name: Unique identifier for this executor state
        executor_class: ThreadPoolExecutor or ProcessPoolExecutor
        max_workers: Number of worker threads/processes
        max_results: Maximum completed results to retain (LRU eviction)

    Returns:
        Shared ExecutorState instance for this name
    """
    with _registry_lock:
        if name not in _executor_states:
            _executor_states[name] = ExecutorState(
                executor=executor_class(max_workers=max_workers),
                max_results=max_results,
            )
        return _executor_states[name]


def shutdown_executor(name: str, wait: bool = True) -> None:
    """Shutdown a shared executor by name.

    WARNING: This shuts down the executor for ALL backend instances
    using the same name. Call only during application shutdown.

    Args:
        name: The executor state name to shutdown
        wait: If True, wait for pending tasks to complete
    """
    with _registry_lock:
        state = _executor_states.pop(name, None)
        if state:
            state.executor.shutdown(wait=wait)
