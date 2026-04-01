#!/bin/bash
set -e

PERSISTENCE_MODE="${PERSISTENCE_MODE:-hybrid}"
RUN_DATABASE_MIGRATIONS="${RUN_DATABASE_MIGRATIONS:-}"
RUN_INITADMIN="${RUN_INITADMIN:-}"
CREATE_DYNAMODB_TABLES="${CREATE_DYNAMODB_TABLES:-false}"
DB_ENGINE="${DB_ENGINE:-}"
DB_NAME="${DB_NAME:-}"

if [ "${DB_ENGINE}" = "sqlite3" ] && [ -n "${DB_NAME}" ]; then
  mkdir -p "$(dirname "${DB_NAME}")"
fi

if [ -z "${RUN_DATABASE_MIGRATIONS}" ]; then
  if [ "${PERSISTENCE_MODE}" = "dynamodb" ]; then
    RUN_DATABASE_MIGRATIONS="false"
  else
    RUN_DATABASE_MIGRATIONS="true"
  fi
fi

if [ -z "${RUN_INITADMIN}" ]; then
  if [ "${PERSISTENCE_MODE}" = "dynamodb" ]; then
    RUN_INITADMIN="false"
  else
    RUN_INITADMIN="true"
  fi
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
