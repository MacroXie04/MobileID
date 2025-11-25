# MobileID

A secure, dual-stack web application for mobile identification and barcode management built with Django and Vue.js.

## Overview

MobileID provides a comprehensive platform for generating, managing, and authenticating PDF417 barcodes with role-based access control.

## Features

- **Dual Authentication System**: Traditional login/password and WebAuthn passwordless authentication
- **Role-Based Access Control**: Separate interfaces for Users, School administrators, and Staff
- **PDF417 Barcode Generation**: Dynamic barcode creation and management
- **User Profile Management**: Avatar upload and profile customization
- **Real-Time Dashboard**: Usage analytics and barcode management interface
- **Long-Term Sessions**: JWT tokens with extended validity for seamless user experience
- **Responsive Design**: Material Design 3 UI components for modern user interface

## Architecture

### Backend (Django REST API)

- **Framework**: Django 5.2+ with Django REST Framework
- **Authentication**: JWT tokens with cookie-based storage
- **Database**: SQLite (development), MySQL/PostgreSQL (production)
- **Security**: WebAuthn integration, CORS configuration, CSRF protection, RSA password encryption

### Frontend (Vue.js SPA)

- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite
- **UI Library**: Material Web Components
- **Routing**: Vue Router with authentication guards
- **Styling**: Material Design 3 principles

## Prerequisites

- Python 3.12+
- Docker Desktop (for local Docker compose workflows)
- Node.js 18+ (if working on the `pages/` frontend)

## Docker (Local Development)

This repo runs the Django API in a single `api` service with Docker. Environment is loaded via `.env.development` by default; production overrides use `docker-compose.prod.yml`.

### Environment

Create or edit `.env.development` at the repository root. Use ONLY localhost origins and connect to your macOS host MySQL via `host.docker.internal`:

```env
ALLOWED_HOSTS=localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://localhost:5173,http://localhost:8080
DB_HOST=host.docker.internal

# Optional DB creds (example for local root)
DB_NAME=mobileid
DB_USER=root
DB_PASSWORD=rootpassword
```

**Important:**

- All browser-visible origins must use `http://localhost` (NOT `127.0.0.1`).
- The API listens on `http://localhost:8000`.

### Run (development)

```bash
docker compose up --build
```

Then visit `http://localhost:8000`.

Common commands:

```bash
# Tail logs
docker compose logs -f api

# Run Django commands inside the container
docker compose exec api python manage.py createsuperuser

# Stop
docker compose down
```

### Run (production override locally)

This uses `gunicorn` with the Uvicorn worker and `.env.production`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

## Settings behavior (env precedence)

`src/core/settings/` contains the settings configuration. `base.py` is shared, while `dev.py` and `prod.py` handle environment-specifics.

Database defaults to MySQL with:

- `DB_HOST=host.docker.internal` to reach host MySQL from the container

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MobileID
```

### 2. Backend Setup

You can run commands from the root `manage.py` or inside `src/`.

```bash
# Install dependencies
cd src/
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env  # or create .env based on examples

# Run database migrations
cd ..
python manage.py makemigrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser
```

### 3. Frontend Setup (optional, not containerized here)

```bash
cd pages/
yarn install          # preferred; matches the repo's packageManager
# or, if you must use npm (package-lock generation is disabled):
npm install
```

## Development

### Starting the Development Servers

#### Backend Server

Using the root `manage.py`:

```bash
python manage.py runserver
```

The Django API will be available at `http://localhost:8000` (use localhost, not 127.0.0.1).

#### Frontend Server

```bash
cd pages/
yarn dev
# or
npm run dev
```

The Vue.js application will be available at `http://localhost:5173`.

### Code Quality

#### Frontend Linting and Formatting

```bash
cd pages/
yarn lint           # Check for linting errors
yarn format         # Format code with Prettier
```

#### Backend CI/CD pipeline

Backend automation is serialized so every backend check passes before a deploy:

1. `Lint Ruff` (`.github/workflows/lint_ruff.yml`) runs on each push/PR touching backend code.
2. `Django Tests` (`.github/workflows/django_tests.yml`) starts only after Ruff succeeds.
3. `Database Migrations` (`.github/workflows/database_migrations.yml`) runs after the Django test suite passes to ensure migrations remain in sync.
4. `Deploy to Cloud Run` (`.github/workflows/gcp_deploy.yml`) now triggers from the completed migrations workflow, so production deployments only occur after the entire backend chain passes on `main`.

Each chained workflow deploys the exact commit that passed the previous step by reusing `github.event.workflow_run.head_sha`.

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the `src/` directory.

#### Core Settings

| Variable     | Description          | Default               | Required         |
| ------------ | -------------------- | --------------------- | ---------------- |
| `SECRET_KEY` | Django secret key    | `dev-secret`          | Yes (Production) |
| `DEBUG`      | Enable debug mode    | `False`               | No               |
| `TESTING`    | Enable test mode     | `False`               | No               |
| `TIME_ZONE`  | Application timezone | `America/Los_Angeles` | No               |

#### Database Configuration

| Variable             | Description                      | Default | Required |
| -------------------- | -------------------------------- | ------- | -------- |
| `DB_PROFILE`         | Database profile (`local`/`gcp`) | `local` | No       |
| `DATABASE_URL_LOCAL` | Connection string for local      |         | No       |
| `DATABASE_URL_GCP`   | Connection string for GCP        |         | No       |

## API Endpoints

### Authentication

- `POST /authn/login/` - User login (RSA encrypted)
- `POST /authn/register/` - User registration
- `POST /authn/logout/` - User logout
- `GET /authn/user-info/` - Get current user information

### Barcode Management

- `POST /generate_barcode/` - Generate new barcode
- `GET /active_profile/` - Get active barcode profile
- `GET /barcode_dashboard/` - Get barcode dashboard data

## License

This project is proprietary software. All rights reserved.
