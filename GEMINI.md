# MobileID - Project Context & Instructions

MobileID is a secure dual-stack monorepo for mobile identification and barcode management. It consists of a Django-based REST API and a Vue.js single-page application (SPA).

## Project Overview
- **Backend**: Django 5.2+ REST API (`src/`) using PostgreSQL and DynamoDB.
- **Frontend**: Vue 3 SPA with Vite (`pages/`) using Material Design Components.
- **Infrastructure**: Local development via Docker Compose; production deployment on AWS (ECS Fargate for backend, Amplify for frontend).
- **Core Features**: PDF417 barcode generation, profile management, and device-aware authentication (JWT + WebAuthn).

## Architecture & Structure

```
MobileID/
├── src/                        # Django Backend
│   ├── authn/                  # Authentication (JWT + WebAuthn)
│   ├── index/                  # Core barcode and profile logic
│   ├── core/                   # Project configuration and shared utilities
│   │   ├── settings/           # Modularized Django settings (base, auth, security, etc.)
│   │   ├── dynamodb/           # DynamoDB client and table definitions
│   │   └── middleware/         # Custom security and audit middleware
│   └── manage.py
├── pages/                      # Vue 3 Frontend
│   ├── src/
│   │   ├── features/           # Feature-organized logic (auth, barcode, user-profile)
│   │   ├── shared/             # Common components, composables, and API clients
│   │   └── app/                # Main app entry and router configuration
│   └── package.json
├── infra/                      # Database exports and infrastructure scripts
├── ops/                        # AWS-specific deployment templates and scripts
└── docker-compose.yml          # Local development orchestration
```

## Local Development

### Environment Setup
- **Docker (Recommended)**: `docker compose up --build`
  - API: `http://localhost:8000`
  - Use `localhost`, not `127.0.0.1` for local development.
- **Manual Backend Setup**:
  - `cd src && pip install -r requirements-dev.txt`
  - `cp .env.example .env`
  - `python manage.py migrate`
  - `python manage.py create_dynamodb_tables`
  - `python manage.py runserver`
- **Manual Frontend Setup**:
  - `cd pages && yarn install`
  - `yarn dev` (Runs at `http://localhost:5173`)

### Database Access
- **PostgreSQL**: Used for primary relational data.
- **DynamoDB Local**: Used for barcodes, transactions, and security-sensitive auth data. Managed via `src/core/dynamodb/`.

## Key Commands

### Backend
- **Run Tests**: `python manage.py test`
- **Linting**: `ruff check .` and `flake8 .`
- **Formatting**: `black .`
- **Migrations**: `python manage.py makemigrations` and `python manage.py migrate`
- **Create Superuser**: `python manage.py createsuperuser`

### Frontend
- **Unit Tests**: `yarn test:unit`
- **E2E Tests**: `yarn test:e2e` (Playwright)
- **Linting**: `yarn lint`
- **Formatting**: `yarn format`

## Development Conventions

### Coding Standards
- **Backend**: Adhere to PEP 8; use Ruff for linting. Django settings are modularized in `src/core/settings/`.
- **Frontend**: Use Vue 3 Composition API. Follow the feature-based directory structure in `pages/src/features/`.
- **API**: Use Django REST Framework. Authentication is handled via SimpleJWT.

### Testing & Quality
- **Mandatory Verification**: Always run backend migrations with `--check --dry-run` before submitting changes.
- **Test Colocation**: Frontend unit tests are typically colocated with the components they test or placed in `pages/tests/unit`.
- **CI/CD**: The project uses GitHub Actions (`.github/workflows/pipeline.yml`) for linting, migration checks, and automated testing.

### Security
- Protect `.env` files and never commit sensitive credentials.
- Use the custom middleware in `src/core/middleware/` for security-related features like IP whitelisting and CSP.
