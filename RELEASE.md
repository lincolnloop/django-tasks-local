# Releasing

## Development Setup

Install pre-commit hooks to catch formatting errors before committing:

```bash
uv run pre-commit install
```

## Publishing to PyPI

Requires PyPI credentials in your keyring (see below).

Tag the current release and push it:

```bash
git pull
git tag --list "v*"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push --tags
```

Build and publish:

```bash
rm -rf dist
uv build
uv publish
```

## PyPI Credentials Setup

Install keyring (used by uv for publishing) and set your token:

```bash
uv tool install keyring
keyring set 'https://upload.pypi.org/legacy/' __token__
```

Add these environment variables to your shell:

```bash
export UV_KEYRING_PROVIDER=subprocess
export UV_PUBLISH_USERNAME=__token__
```
