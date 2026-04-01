# MobileID — Claude Code Guide

## Project Overview

Secure dual-stack web app for mobile identification and barcode management.

- **Backend**: Django 5.2+ REST API (`src/`)
- **Frontend**: Vue 3 SPA with Vite (`pages/`)
- **Deployment**: AWS ECS Fargate (backend) + AWS Amplify (frontend)

## Architecture

```
MobileID/
├── src/                        # Django backend
│   ├── authn/                  # Authentication (JWT + WebAuthn)
│   ├── index/                  # Core barcode/profile logic
│   ├── core/                   # Settings, shared utilities
│   └── manage.py
├── pages/                      # Vue 3 frontend
│   └── src/features/dashboard/ # Main dashboard feature
├── docker-compose.yml
└── .env.development            # Local dev env vars
```

## Local Development

### Run with Docker (preferred)

```bash
docker compose up --build
```

API at `http://localhost:8000`. Always use `localhost`, not `127.0.0.1`.

### Backend only

```bash
cd src/
pip install -r requirements.txt
cd ..
python manage.py migrate
python manage.py runserver
```

### Frontend only

```bash
cd pages/
yarn install
yarn dev   # http://localhost:5173
```

## Environment Variables

Create `.env.development` at the repo root for Docker. Key vars:

```env
ALLOWED_HOSTS=localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://localhost:5173,http://localhost:8080
DB_HOST=host.docker.internal
DB_NAME=mobileid
DB_USER=root
DB_PASSWORD=rootpassword
```

## Key Commands

```bash
# Django management inside Docker
docker compose exec api python manage.py createsuperuser
docker compose exec api python manage.py migrate

# Frontend linting
cd pages/ && yarn lint && yarn format
```

## CI/CD

- **Backend CI** (`.github/workflows/backend_ci.yml`): lint, migration check, Django tests — runs in parallel on PRs
- **Deploy** (`.github/workflows/aws_backend_deploy.yml`): triggers on pushes to `main` that touch `src/`

## Settings

`src/core/settings/` — `base.py` shared, `dev.py` and `prod.py` for environment-specific config. PostgreSQL via docker-compose; DynamoDB for barcode/transaction/auth security data.