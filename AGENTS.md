# Repository Guidelines

## Project Structure & Module Organization

MobileID is a monorepo with a Django API in `src/` and a Vue 3/Vite SPA in `pages/`. Backend apps are organized by domain under `src/authn`, `src/core`, and `src/index`, with tests colocated in each app or service package. Frontend code lives in `pages/src`, split into `app`, `features/*`, `shared/*`, `assets`, and `test`; use the configured aliases such as `@auth`, `@dashboard`, and `@shared`. End-to-end tests are in `pages/tests/e2e`, and deployment/runtime config includes `docker-compose.yml`, `src/Dockerfile`, and `pages/vercel.json`.

## Build, Test, and Development Commands

- `cd src && python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`: set up backend development dependencies.
- `cd src && python manage.py migrate && python manage.py runserver`: run the local API at `http://localhost:8000`.
- `docker compose up --build`: start Django, Postgres, and DynamoDB Local together.
- `cd pages && yarn install && yarn dev`: run the SPA at `http://localhost:5173`.
- `cd pages && yarn build`: create the production frontend bundle.

## Coding Style & Naming Conventions

Python is formatted with Black and checked with Flake8 and Ruff; Flake8 uses an 88-character line limit and excludes migrations. Keep Django modules domain-oriented and name tests `test_*.py`. Frontend code uses ESLint plus Prettier with single quotes, semicolons, trailing commas, and a 100-character print width. Vue components use PascalCase filenames where practical; composables should start with `use`, for example `useDashboardLogic.js`.

## Testing Guidelines

Run backend checks from `src/`: `python manage.py makemigrations --check --dry-run`, `coverage run manage.py test -v 2`, and `coverage report --fail-under=70`. Run frontend checks from `pages/`: `yarn lint`, `yarn test:unit`, and `yarn test:e2e:ci`. Vitest picks up `*.spec.js` and `*.spec.ts` under `pages/src`; Playwright specs live under `pages/tests/e2e`.

## Commit & Pull Request Guidelines

Recent history uses short, imperative, lower-case commit subjects, such as `fix CI lint failures: apply black and prettier formatting`. Keep commits focused by backend, frontend, or infrastructure concern. Pull requests should include a concise change summary, affected areas, linked issues when available, screenshots for UI changes, and the exact checks run locally. Avoid modifying already-created migration files unless the change intentionally includes a new migration path.

## Security & Configuration Tips

Use `src/.env.example` as the backend template and never commit secrets. Production frontend builds require `VITE_API_BASE_URL`; Django production settings require a real `SECRET_KEY` and database configuration.
