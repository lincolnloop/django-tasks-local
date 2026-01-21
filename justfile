# Install dependencies
# Run tests (with coverage)
test *args:
    uv run pytest --cov=tasks_threadpool --cov-report=term-missing {{ args }}

# Lint and format check
lint:
    uvx ruff check
    uvx ruff format --check

# Format code
fmt:
    uvx ruff format
    uvx ruff check --fix

# Build package
build:
    uv build

# Serve docs locally
docs:
    uv run --group docs zensical serve

# Run example app
example:
    uv run example.py
