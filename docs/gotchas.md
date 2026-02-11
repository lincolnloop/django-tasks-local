# Gotchas

## In-Memory Only

**This is the main limitation to understand.**

All task results and the pending task queue exist only in memory. When your process restarts:

- All pending tasks are lost
- All completed task results are gone
- There's no way to recover them

This package is designed for development and low-volume production where losing tasks on restart is acceptable. If you need persistence, use [django-tasks](https://pypi.org/project/django-tasks/) with `DatabaseBackend` or `RQBackend`.

## LRU Eviction

When `MAX_RESULTS` is exceeded, the oldest completed results are evicted. If you try to retrieve an evicted result, you'll get `TaskResultDoesNotExist`.

Tune `MAX_RESULTS` based on your needs, but remember it all lives in memory.

## ProcessPoolBackend: No Shared State

Each process has its own memory space. Global variables modified in a task won't affect the parent process:

```python
counter = 0

@task
def increment():
    global counter
    counter += 1  # Only affects this process's copy
    return counter

# In parent process:
increment.enqueue()  # Returns 1
print(counter)       # Still 0 in parent
```

This is by design - it's how multiprocessing works. Use a database or cache for shared state.
