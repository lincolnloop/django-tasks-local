"""
django-tasks-local: Zero-infrastructure task backends for Django 6.

Provides ThreadPoolBackend and ProcessPoolBackend for background task
execution using Python's standard concurrent.futures module.

No Redis, Celery, or database required.
"""

from .backend import (
    ProcessPoolBackend,
    ThreadPoolBackend,
    current_result_id,
)

__all__ = [
    "ThreadPoolBackend",
    "ProcessPoolBackend",
    "current_result_id",
]
