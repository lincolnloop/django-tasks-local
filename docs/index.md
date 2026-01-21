# django-tasks-local

Zero-infrastructure task backends for Django 6.

## Why?

Django 6 ships with `ImmediateBackend` (blocks the request) and `DummyBackend` (does nothing).

This package provides **background execution with zero infrastructure**:

- **ThreadPoolBackend** - Tasks run in a thread pool (best for I/O-bound work)
- **ProcessPoolBackend** - Tasks run in a process pool (best for CPU-bound work)

No Redis, Celery, or database required. Ideal for development and low-volume production.

## Installation

```bash
pip install django-tasks-local
```

## Quick Start

```python
# settings.py
TASKS = {
    "default": {"BACKEND": "django_tasks_local.ThreadPoolBackend"},
}
```

```python
# views.py
from django.tasks import task

@task
def send_welcome_email(user_id):
    # This runs in a background thread
    ...

# In your view
send_welcome_email.enqueue(user.id)
```

## Choosing a Backend

| Use Case | Backend | Why |
|----------|---------|-----|
| Sending emails, API calls, database operations | `ThreadPoolBackend` | I/O-bound tasks benefit from threading |
| Image processing, data analysis, PDF generation | `ProcessPoolBackend` | CPU-bound tasks need true parallelism (bypasses GIL) |

## Limitations

- **In-memory only** - Results are lost on restart
- **No scheduled execution** - `supports_defer = False`
- **No priority** - Tasks execute in FIFO order
- **No native async** - `supports_async_task = False`

See [Gotchas](gotchas.md) for edge cases to be aware of.
