# UV Package Manager - Quick Reference

This project uses **uv** for Python package management.

## Setup (First Time)

```bash
cd src/
uv sync --all-extras
```

## Daily Development

```bash
# Run Django dev server
uv run python manage.py runserver

# Or activate venv once
source .venv/bin/activate
python manage.py runserver
```

## Common Commands

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --all-extras` |
| Run Django server | `uv run python manage.py runserver` |
| Run tests | `TESTING=True uv run python manage.py test` |
| Run migrations | `uv run python manage.py migrate` |
| Format code | `uv run black .` |
| Lint code | `uv run ruff check .` |
| Add package | `uv add package-name` |
| Add dev package | `uv add --dev package-name` |

## Files Overview

- `pyproject.toml` - Project config & dependencies
- `uv.lock` - Locked versions (commit this!)
- `.venv/` - Virtual environment (don't commit)
- `.python-version` - Python version (3.12.7)

## Why UV?

✅ 10-100x faster than pip  
✅ Deterministic builds with lockfile  
✅ Automatic virtual environment management  
✅ Modern, reliable dependency resolution

For full documentation, see `UV_SETUP.md`
