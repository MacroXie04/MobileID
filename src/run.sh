#!/bin/bash
set -e

PERSISTENCE_MODE="${PERSISTENCE_MODE:-hybrid}"
RUN_DATABASE_MIGRATIONS="${RUN_DATABASE_MIGRATIONS:-}"
RUN_INITADMIN="${RUN_INITADMIN:-}"
CREATE_DYNAMODB_TABLES="${CREATE_DYNAMODB_TABLES:-false}"
DB_ENGINE="${DB_ENGINE:-}"
DB_NAME="${DB_NAME:-}"

if [ "${PERSISTENCE_MODE}" = "dynamodb" ]; then
  echo "PERSISTENCE_MODE=dynamodb is not supported by the current runtime." >&2
  echo "Auth, profile, session, token, and device-management flows still require SQL." >&2
  echo "Use PERSISTENCE_MODE=hybrid until the full DynamoDB migration is implemented." >&2
  exit 1
fi

if [ "${DB_ENGINE}" = "sqlite3" ] && [ -n "${DB_NAME}" ]; then
  mkdir -p "$(dirname "${DB_NAME}")"
fi

if [ -z "${RUN_DATABASE_MIGRATIONS}" ]; then
  RUN_DATABASE_MIGRATIONS="true"
fi

if [ -z "${RUN_INITADMIN}" ]; then
  RUN_INITADMIN="true"
fi

if [ "${CREATE_DYNAMODB_TABLES}" = "true" ]; then
  echo "Ensuring DynamoDB tables exist..."
  python manage.py create_dynamodb_tables
fi

if [ "${RUN_DATABASE_MIGRATIONS}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate
else
  echo "Skipping migrations (PERSISTENCE_MODE=${PERSISTENCE_MODE})..."
fi

if [ "${RUN_INITADMIN}" = "true" ]; then
  echo "Checking/Creating superuser..."
  python manage.py initadmin
else
  echo "Skipping initadmin bootstrap (PERSISTENCE_MODE=${PERSISTENCE_MODE})..."
fi

echo "Starting Gunicorn..."
exec gunicorn --bind :8080 \
    --workers "${GUNICORN_WORKERS:-1}" \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    core.wsgi:application
