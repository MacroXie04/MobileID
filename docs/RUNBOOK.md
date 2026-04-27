# MobileID Runbook

This runbook captures the minimum operational checklist for deploying and
rolling back the MobileID Django API and Vue/Vite SPA.

## Required Production Configuration

Backend:

- `DJANGO_SETTINGS_MODULE=core.settings.prod`
- `SECRET_KEY` set to a unique production value
- `ALLOWED_HOSTS` set to the API hostnames
- `BACKEND_ORIGIN` set to the public API origin
- `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` set to the SPA origins
- `ADMIN_URL_PATH` set to a non-default path
- `DATABASE_URL` or the matching `DATABASE_URL_*` value for the selected `DB_PROFILE`
- `DYNAMODB_REGION`, `DYNAMODB_TABLE_PREFIX`, and IAM permissions for all MobileID DynamoDB tables
- `CACHE_BACKEND` and `CACHE_LOCATION` set to a shared cache for multi-worker production deployments

Frontend:

- `VITE_API_BASE_URL` set to the public backend API origin

## Pre-Deploy Checks

Run backend checks from `src/`:

```bash
python manage.py makemigrations --check --dry-run
coverage run manage.py test -v 2
coverage report --fail-under=70
black --check .
flake8 .
ruff check .
bandit -r authn core index -x '*/tests/*,*/migrations/*' -ll
```

Run frontend checks from `pages/`:

```bash
yarn lint
yarn typecheck
yarn test:unit
yarn build
```

Run Playwright E2E before promoting a user-facing release:

```bash
yarn test:e2e:ci
```

## Health Probes

- `/livez/`: process liveness only. Use for container liveness probes.
- `/readyz/`: dependency readiness. Use for rollout readiness gates.
- `/health/`: human and monitoring health endpoint with dependency status.
- `/openapi.json`: generated API schema for clients and release review.

Expected ready response:

```json
{
  "status": "healthy",
  "service": "MobileID",
  "persistence_mode": "hybrid",
  "database": "connected",
  "dynamodb": "connected",
  "cache": "connected",
  "probe": "readiness"
}
```

Any `/readyz/` 503 means the instance should not receive traffic.

## Deploy

1. Verify CI `Pipeline Passed` and CodeQL are green for the release commit.
2. Build and publish the backend image from `src/Dockerfile`.
3. Apply database migrations before shifting traffic:

   ```bash
   python manage.py migrate --noinput
   ```

4. Create or validate DynamoDB tables:

   ```bash
   python manage.py create_dynamodb_tables
   ```

5. Deploy the backend image.
6. Wait for `/readyz/` to return 200 on new instances.
7. Deploy the frontend with the matching `VITE_API_BASE_URL`.
8. Smoke test login, dashboard load, barcode generation, and profile update.

## Rollback

Backend rollback:

1. Stop traffic shift to the new backend revision.
2. Restore the last known-good image.
3. Confirm `/livez/` and `/readyz/` return 200.
4. Check application logs by `request_id` for continuing 5xx responses.

Database rollback:

- Prefer forward fixes for migrations that already ran in production.
- If a schema migration must be rolled back, verify the reverse migration locally against a production-like copy first.
- Do not delete DynamoDB tables as part of normal rollback. Disable the new code path or restore the prior image instead.

Frontend rollback:

1. Promote the last known-good Vercel deployment.
2. Confirm the SPA loads and protected routes redirect correctly when unauthenticated.
3. Confirm the deployed frontend still points to the intended backend origin.

## Incident Triage

- Use the `X-Request-ID` response header to correlate client reports with backend logs.
- For auth failures, inspect `/authn/user_info/`, token refresh, and CORS/CSRF origin configuration first.
- For barcode generation failures, check DynamoDB availability, duplicate barcode validation, and transaction usage limits.
- For slow dashboard loads, inspect bounded shared barcode reads and DynamoDB throttling or timeout errors.
