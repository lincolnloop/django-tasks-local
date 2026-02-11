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

**Raises:** `TypeError` if arguments cannot be converted to JSON.

### `get_result(result_id)`

Retrieve a task result by its UUID string.

**Returns:** `TaskResult` with current status.

**Raises:** `TaskResultDoesNotExist` if not found (never existed or was evicted).

### `close()`

Shut down the executor.

**Warning:** This shuts down the executor for ALL backend instances using the same alias. Only call during application shutdown.
