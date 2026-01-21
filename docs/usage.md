# Usage

## Configuration

### ThreadPoolBackend

Best for I/O-bound tasks (network, disk, database).

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks_local.ThreadPoolBackend",
        "OPTIONS": {
            "MAX_WORKERS": 10,    # Thread pool size (default: 10)
            "MAX_RESULTS": 1000,  # Results to keep in memory (default: 1000)
        }
    }
}
```

### ProcessPoolBackend

Best for CPU-bound tasks (image processing, data crunching).

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks_local.ProcessPoolBackend",
        "OPTIONS": {
            "MAX_WORKERS": 4,     # Process pool size (default: 10)
            "MAX_RESULTS": 1000,
        }
    }
}
```

**Note:** ProcessPoolBackend requires task arguments and return values to be [pickleable](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled).

### Multiple Backends

Route different tasks to different backends:

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks_local.ThreadPoolBackend",
    },
    "cpu_intensive": {
        "BACKEND": "django_tasks_local.ProcessPoolBackend",
        "OPTIONS": {"MAX_WORKERS": 4},
    }
}
```

```python
@task(backend="cpu_intensive")
def process_image(image_path):
    # Runs in a separate process
    ...
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `MAX_WORKERS` | 10 | Number of threads/processes in the pool |
| `MAX_RESULTS` | 1000 | Maximum results to keep (LRU eviction when exceeded) |

## Accessing Task Result ID

Tasks can access their own result ID via a context variable:

```python
from django.tasks import task
from django_tasks_local import current_result_id

@task
def my_task():
    result_id = current_result_id.get()
    # Use for logging, progress tracking, etc.
```

This works in both ThreadPoolBackend and ProcessPoolBackend.

## Retrieving Results

```python
from django.tasks import task

@task
def add(a, b):
    return a + b

# Enqueue and get result object
result = add.enqueue(2, 3)
print(result.id)      # UUID string
print(result.status)  # READY initially

# Refresh to get latest status
result.refresh()
print(result.status)  # RUNNING or SUCCESSFUL

# Or retrieve by ID
from django.tasks import default_task_backend

result = default_task_backend.get_result(result_id)
print(result.status)        # TaskResultStatus.SUCCESSFUL
print(result.return_value)  # 5
```

## Task Status Lifecycle

```
READY → RUNNING → SUCCESSFUL
                → FAILED
```

- **READY** - Task is queued, waiting for a worker
- **RUNNING** - Task is currently executing
- **SUCCESSFUL** - Task completed, `return_value` available
- **FAILED** - Task raised an exception, `errors` contains details
