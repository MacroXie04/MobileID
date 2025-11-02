# UV Package Manager Setup

This project now uses `uv` for Python package management - a fast, reliable alternative to pip and pip-tools.

## Why UV?

- **Fast**: 10-100x faster than pip
- **Reliable**: Deterministic dependency resolution with lockfile
- **All-in-one**: Replaces pip, pip-tools, virtualenv, and more
- **Compatible**: Works with existing pyproject.toml and requirements.txt

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv

# Or with Homebrew
brew install uv
```

## Quick Start

```bash
cd src/

# Install all dependencies (creates .venv automatically)
uv sync

# Install with dev dependencies
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Run Django commands
uv run python manage.py runserver
uv run python manage.py test
```

## Common Tasks

### Managing Dependencies

```bash
# Add a new package
uv add django-package-name

# Add a dev dependency
uv add --dev pytest-package-name

# Remove a package
uv remove package-name

# Update all dependencies
uv lock
uv sync

# Update a specific package
uv add django-package-name --upgrade
```

### Running Commands

```bash
# Run without activating venv
uv run python manage.py runserver
uv run pytest
uv run black .

# Or activate venv first
source .venv/bin/activate
python manage.py runserver
```

### Development Workflow

```bash
# 1. Clone repo and setup
git clone <repo>
cd src/
uv sync --all-extras

# 2. Run migrations
uv run python manage.py migrate

# 3. Create superuser
uv run python manage.py createsuperuser

# 4. Start dev server
uv run python manage.py runserver

# 5. Run tests
TESTING=True uv run pytest
# or
TESTING=True uv run python manage.py test
```

### Linting and Formatting

```bash
# Format code with black
uv run black .

# Lint with ruff
uv run ruff check .

# Lint with flake8
uv run flake8 .

# Run all checks
uv run black --check . && uv run ruff check . && uv run flake8 .
```

## Configuration Files

- **`pyproject.toml`**: Project metadata and dependencies
- **`uv.lock`**: Lockfile with exact versions (commit this!)
- **`.python-version`**: Python version specification
- **`.venv/`**: Virtual environment (do NOT commit)

## Migration from pip

The old `requirements.txt` is kept for reference but no longer used. All dependencies are now in `pyproject.toml`:

```toml
[project]
dependencies = [
    "Django>=5.2,<6.0",
    # ... other packages
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "black>=24.0",
    # ... dev tools
]
```

## CI/CD Integration

Update your CI workflows to use uv:

```yaml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync --all-extras

- name: Run tests
  run: uv run pytest
```

## Troubleshooting

### "uv: command not found"
Install uv using one of the methods above, then restart your shell.

### Virtual environment issues
```bash
# Remove and recreate venv
rm -rf .venv
uv sync
```

### Dependency conflicts
```bash
# Update lockfile
uv lock --upgrade

# Force reinstall
rm -rf .venv uv.lock
uv sync
```

## Learn More

- Official docs: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
