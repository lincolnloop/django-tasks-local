# django-tasks-local

Zero-infrastructure task backends for Django 6.

Django 6 ships with `ImmediateBackend` (blocks the request) and `DummyBackend` (does nothing). This package provides **background execution with zero infrastructure**:

- **ThreadPoolBackend** - I/O-bound tasks (emails, API calls, database)
- **ProcessPoolBackend** - CPU-bound tasks (image processing, data analysis)

No Redis, Celery, or database required.

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
from django.tasks import task

@task
def send_welcome_email(user_id):
    ...

send_welcome_email.enqueue(user.id)
```

## Documentation

- [Usage Guide](https://lincolnloop.github.io/django-tasks-local/usage/) - Configuration, multiple backends, retrieving results
- [API Reference](https://lincolnloop.github.io/django-tasks-local/api/) - Backend capabilities and methods
- [Gotchas](https://lincolnloop.github.io/django-tasks-local/gotchas/) - Limitations and edge cases

## Limitations

- **In-memory only** - Results lost on restart
- **No scheduling** - `supports_defer = False`
- **No priority** - FIFO execution

For persistence, see [django-tasks](https://pypi.org/project/django-tasks/) which provides `DatabaseBackend` and `RQBackend`.
