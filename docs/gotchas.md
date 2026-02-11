# Gotchas

## In-Memory Only

**This is the main limitation to understand.**

All task results and the pending task queue exist only in memory. When your process restarts:

- All pending tasks are lost
- All completed task results are gone
- There's no way to recover them

This package is designed for development and low-volume production where losing tasks on restart is acceptable. For persistence, see [django-tasks-db](https://pypi.org/project/django-tasks-db/) or [django-tasks-rq](https://pypi.org/project/django-tasks-rq/).


## LRU Eviction

When `MAX_RESULTS` is exceeded, the oldest completed results are evicted. If you try to retrieve an evicted result, you'll get `TaskResultDoesNotExist`.

Tune `MAX_RESULTS` based on your needs, but remember it all lives in memory.

## ProcessPoolBackend: Pickling Required

ProcessPoolBackend uses Python's `ProcessPoolExecutor`, which requires all data crossing process boundaries to be [pickleable](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled).

**What must be pickleable:**

- Task arguments
- Task return values
- Task functions (must be defined at module level)

**Common unpickleable objects:**

- Lambda functions
- Nested functions (defined inside other functions)
- Open file handles, database connections
- Certain Django objects (QuerySets, etc.)

```python
# This will raise ValueError at enqueue time:
backend.enqueue(my_task, args=(lambda x: x,))

# This will fail when the task returns:
@task
def bad_task():
    return lambda x: x  # Can't pickle lambda
```

**Workaround:** Pass IDs instead of objects, and fetch them inside the task:

```python
# Instead of passing the queryset:
@task
def process_users(user_ids):
    users = User.objects.filter(id__in=user_ids)
    ...

# Enqueue with IDs
process_users.enqueue(list(User.objects.values_list('id', flat=True)))
```

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

## ContextVars in Child Threads

If your task spawns additional threads, those threads won't inherit ContextVar values:

```python
from django.tasks import task
from django_tasks_local import current_result_id
import threading

@task
def my_task():
    # Works - we're in the worker thread/process
    result_id = current_result_id.get()  # ✓

    def child_work():
        # Fails - child thread has empty context
        result_id = current_result_id.get()  # ✗ LookupError

    t = threading.Thread(target=child_work)
    t.start()
```

**Workaround:** Copy the context explicitly:

```python
import contextvars

@task
def my_task():
    ctx = contextvars.copy_context()
    t = threading.Thread(target=ctx.run, args=(child_work,))
    t.start()
```

Most tasks don't spawn threads, so this rarely comes up.
