# MobileID

MobileID is a monorepo for a Django API and a Vue/Vite single-page app used for mobile identification, PDF417 barcode generation, profile management, and device-aware authentication flows.

## Structure

- `src/`: Django backend, settings, REST endpoints, DynamoDB helpers, and backend tests.
- `pages/`: Vue 3 SPA, feature-organized frontend code, colocated unit tests, Playwright e2e tests, and `vercel.json` SPA rewrites.
- `docker-compose.yml`: local backend stack with Django, Postgres, and DynamoDB Local.
- `.github/workflows/pipeline.yml`: primary CI pipeline for lint, tests, builds, and security checks.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Yarn 1.x
- Docker Desktop, if you want the full local backend stack

## Backend Setup

```bash
cd src
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
```

If you are running against DynamoDB Local outside Docker, set `DYNAMODB_ENDPOINT_URL` in `src/.env` and run:

```bash
python manage.py create_dynamodb_tables
```

To start the backend directly:

```bash
python manage.py runserver
```

The API is served at `http://localhost:8000`.

## Frontend Setup

```bash
cd pages
yarn install
yarn dev
```

The SPA runs at `http://localhost:5173`.

For production builds, `VITE_API_BASE_URL` must be set. The frontend intentionally throws if a production build is missing that value.

## Docker Development

The included Compose stack starts Django, Postgres, and DynamoDB Local:

```bash
docker compose up --build
```

Useful follow-up commands:

```bash
docker compose logs -f backend
docker compose exec backend python manage.py createsuperuser
docker compose down
```

## Testing And Quality Checks

Backend:

```bash
cd src
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
black --check .
flake8 .
ruff check .
```

Frontend:

```bash
cd pages
yarn lint
yarn test:unit
yarn test:e2e:ci
```

## CI

`pipeline.yml` is the active workflow. It runs:

- backend lint (Black, Flake8, Ruff) and frontend lint (Prettier, ESLint) in parallel
- migration file guard on pull requests
- Django migration checks and Django tests with coverage (`--fail-under=70`)
- frontend unit tests and Playwright E2E tests
- backend Docker build and frontend Vite build
- dependency and image security scans: Safety, Yarn audit, Trivy
- a `Pipeline Passed` summary gate that fails if any required job — build, test, or security — does not succeed

## Configuration Notes

- Backend environment examples live in `src/.env.example`.
- The frontend base URL logic lives in `pages/src/app/config/config.js`.
- SPA rewrites for Vercel are defined in `pages/vercel.json`.

## License

This project is proprietary software. All rights reserved.
