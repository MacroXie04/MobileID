# Development Setup

## Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js 18+ with Yarn 1.x
- Docker (optional, for PostgreSQL)

## Quick Start

### Backend

```bash
cd src
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py generate_rsa_keypair
uv run python manage.py runserver
```

### Frontend

```bash
cd pages
yarn install
yarn dev
```

### Docker (backend + PostgreSQL)

```bash
docker compose up --build
```

## Running Tests

```bash
# Backend
cd src && uv run python manage.py test -v 2

# Frontend
cd pages && yarn test:unit
```

## Code Quality

```bash
# Backend
cd src && uv run black --check . && uv run ruff check . && uv run flake8 .

# Frontend
cd pages && yarn lint && yarn format
```
