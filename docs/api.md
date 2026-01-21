# API Reference

## Backends

Both backends share the same interface, inheriting from Django's `BaseTaskBackend`.

### ThreadPoolBackend

```python
from django_tasks_local import ThreadPoolBackend
```

Executes tasks in a `ThreadPoolExecutor`. Best for I/O-bound tasks.

### ProcessPoolBackend

```python
from django_tasks_local import ProcessPoolBackend
```

Executes tasks in a `ProcessPoolExecutor`. Best for CPU-bound tasks.

**Constraint:** Arguments and return values must be pickleable.

## Backend Capabilities

| Attribute | Value | Description |
|-----------|-------|-------------|
| `supports_defer` | `False` | No scheduled/delayed execution |
| `supports_async_task` | `False` | No native async support |
| `supports_get_result` | `True` | Results can be retrieved by ID |
| `supports_priority` | `False` | Tasks execute in FIFO order |

## Methods

### `enqueue(task, args=None, kwargs=None)`

Enqueue a task for background execution.

**Returns:** `TaskResult` with initial status `READY`.

**Raises:** `ValueError` if using ProcessPoolBackend with unpickleable arguments.

### `get_result(result_id)`

Retrieve a task result by its UUID string.

**Returns:** `TaskResult` with current status.

**Raises:** `TaskResultDoesNotExist` if not found (never existed or was evicted).

### `close()`

Shut down the executor.

**Warning:** This shuts down the executor for ALL backend instances using the same alias. Only call during application shutdown.

## Context Variable

### `current_result_id`

```python
from django_tasks_local import current_result_id
```

A `ContextVar[str]` holding the current task's result ID. Only available within a running task.

```python
from django.tasks import task
from django_tasks_local import current_result_id

@task
def my_task():
    result_id = current_result_id.get()
    # Use for logging, caching progress, etc.
```

Works in both ThreadPoolBackend and ProcessPoolBackend.
