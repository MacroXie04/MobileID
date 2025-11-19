# MobileID

A secure, dual-stack web application for mobile identification and barcode management built with Django and Vue.js.

## Overview

MobileID provides a comprehensive platform for generating, managing, and authenticating PDF417 barcodes with role-based
access control.

## Features

- **Dual Authentication System**: Traditional login/password and WebAuthn passwordless authentication
- **Role-Based Access Control**: Separate interfaces for Users and School administrators
- **PDF417 Barcode Generation**: Dynamic barcode creation and management
- **User Profile Management**: Avatar upload and profile customization
- **Real-Time Dashboard**: Usage analytics and barcode management interface
- **Long-Term Sessions**: JWT tokens with extended validity for seamless user experience
- **Responsive Design**: Material Design 3 UI components for modern user interface

## Architecture

### Backend (Django REST API)

- **Framework**: Django 5.2+ with Django REST Framework
- **Authentication**: JWT tokens with cookie-based storage
- **Database**: SQLite (development) with PostgreSQL/MySQL support
- **Security**: WebAuthn integration, CORS configuration, CSRF protection

### Frontend (Vue.js SPA)

- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite
- **UI Library**: Material Web Components
- **Routing**: Vue Router with authentication guards
- **Styling**: Material Design 3 principles

## Prerequisites

- Python 3.8+
- Docker Desktop (for local Docker compose workflows)
- Optional: Node.js if you work on the separate `pages/` frontend (not containerized here)

## Docker (Local Development)

This repo runs the Django API in a single `api` service with Docker. Environment is loaded via `.env.development` by
default; production overrides use `docker-compose.prod.yml`.

### Environment

Create or edit `.env.development` at the repository root. Use ONLY localhost origins and connect to your macOS host
MySQL via `host.docker.internal`:

```env
ALLOWED_HOSTS=localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://localhost:5173,http://localhost:8080
DB_HOST=host.docker.internal

# Optional DB creds (example for local root)
DB_NAME=mobileid
DB_USER=root
DB_PASSWORD=rootpassword

# Optional: if you have privileges and want strict SQL modes
# DB_INIT_COMMAND=SET sql_mode='STRICT_ALL_TABLES', innodb_strict_mode=1
```

Important:

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

`src/mobileid/settings.py` prefers real environment variables first, then supplements from `.env` without overriding.
Comma-separated lists are parsed for `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.

Database defaults to MySQL with:

- `DB_HOST=host.docker.internal` to reach host MySQL from the container
- Optional `DB_INIT_COMMAND` to set strict SQL modes only when you have privileges

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MobileID
```

### 2. Backend Setup

```bash
cd src/
pip install -r ../requirements.txt

# Configure environment variables
cp ../.env.example .env
# Edit .env with your configuration (see Configuration section below)

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser
```

**Note**: See the [Environment Variables](#environment-variables) section below for detailed configuration options.

### 3. Frontend Setup (optional, not containerized here)

```bash
cd ../pages/
npm install
# or
yarn install
```

## Development

### Starting the Development Servers

#### Backend Server

```bash
cd src/
python manage.py runserver
```

The Django API will be available at `http://localhost:8000` (use localhost, not 127.0.0.1)

#### Frontend Server

```bash
cd pages/
npm run dev
# or
yarn dev
```

The Vue.js application will be available at `http://localhost:5173`

### Code Quality

#### Frontend Linting and Formatting

```bash
cd pages/
npm run lint        # Check for linting errors
npm run format      # Format code with Prettier
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the `src/` directory with the
following variables:

#### Core Settings

| Variable     | Description                                    | Default               | Required         |
|--------------|------------------------------------------------|-----------------------|------------------|
| `SECRET_KEY` | Django secret key for cryptographic operations | `dev-secret`          | Yes (Production) |
| `DEBUG`      | Enable debug mode (`True`/`False`)             | `False`               | No               |
| `TESTING`    | Enable test mode (`True`/`False`)              | `False`               | No               |
| `TIME_ZONE`  | Application timezone                           | `America/Los_Angeles` | No               |

#### Network & CORS Settings

| Variable                 | Description                                         | Default                                       | Required |
|--------------------------|-----------------------------------------------------|-----------------------------------------------|----------|
| `ALLOWED_HOSTS`          | Comma-separated list of allowed hostnames           | `localhost`                                   | No       |
| `BACKEND_ORIGIN`         | Backend URL                                         | `http://localhost:8000`                       | No       |
| `CORS_ALLOWED_ORIGINS`   | Comma-separated list of frontend URLs for CORS      | `http://localhost:5173,http://localhost:8080` | No       |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS requests (`True`/`False`) | `True`                                        | No       |
| `CSRF_TRUSTED_ORIGINS`   | Comma-separated list of trusted origins for CSRF    | Auto-generated from backend/frontend origins  | No       |

**Important**: Use `http://localhost` (NOT `127.0.0.1`) for all browser-visible origins to avoid CORS issues.

#### Cookie Settings

| Variable               | Description                                                    | Default | Required |
|------------------------|----------------------------------------------------------------|---------|----------|
| `COOKIE_SAMESITE`      | SameSite attribute for session cookies (`Lax`/`Strict`/`None`) | `Lax`   | No       |
| `CSRF_COOKIE_SAMESITE` | SameSite attribute for CSRF cookies                            | `Lax`   | No       |
| `COOKIE_SECURE`        | Require HTTPS for cookies (`True`/`False`)                     | `False` | No       |
| `CSRF_COOKIE_HTTPONLY` | Make CSRF cookie HTTP-only (`True`/`False`)                    | `False` | No       |
| `USE_HTTPS`            | Enable HTTPS-specific settings (`True`/`False`)                | `False` | No       |

#### Database Configuration

**Option 1: Database URL (Recommended)**

| Variable             | Description                             | Example                                                               |
|----------------------|-----------------------------------------|-----------------------------------------------------------------------|
| `DB_PROFILE`         | Database profile to use (`local`/`gcp`) | `local`                                                               |
| `DATABASE_URL_LOCAL` | Database URL for local profile          | `mysql://user:pass@127.0.0.1:3306/dbname`                             |
| `DATABASE_URL_GCP`   | Database URL for GCP profile            | `postgres://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE` |

**Option 2: Discrete Variables (Legacy)**

| Variable      | Description                                           | Default      | Required                     |
|---------------|-------------------------------------------------------|--------------|------------------------------|
| `DB_ENGINE`   | Database engine (`postgresql`/`mysql`/`sqlite3`)      | `postgresql` | No                           |
| `DB_NAME`     | Database name                                         | Empty        | Yes (if using discrete vars) |
| `DB_USER`     | Database user                                         | Empty        | Yes (if using discrete vars) |
| `DB_PASSWORD` | Database password                                     | Empty        | Yes (if using discrete vars) |
| `DB_HOST`     | Database host (use `host.docker.internal` for Docker) | Empty        | Yes (if using discrete vars) |
| `DB_PORT`     | Database port                                         | Empty        | No                           |

**Advanced Database Options**

| Variable                | Description                                                             | Default | Required |
|-------------------------|-------------------------------------------------------------------------|---------|----------|
| `DB_CONN_MAX_AGE`       | Persistent connection lifetime (seconds)                                | `60`    | No       |
| `DB_SSL_MODE`           | SSL mode for database connections (`require`/`verify-ca`/`verify-full`) | Empty   | No       |
| `DB_SSL_DISABLE_VERIFY` | Disable SSL certificate verification (`True`/`False`)                   | `False` | No       |
| `CLOUDSQL_UNIX_SOCKET`  | Unix socket path for Cloud SQL connections                              | Empty   | No       |

#### Security Settings

| Variable                    | Description                                  | Default | Required |
|-----------------------------|----------------------------------------------|---------|----------|
| `MAX_FAILED_LOGIN_ATTEMPTS` | Maximum failed login attempts before lockout | `5`     | No       |
| `ACCOUNT_LOCKOUT_DURATION`  | Account lockout duration in minutes          | `30`    | No       |

#### Cache & Session Settings

| Variable         | Description                | Default                                         | Required |
|------------------|----------------------------|-------------------------------------------------|----------|
| `CACHE_BACKEND`  | Django cache backend class | `django.core.cache.backends.locmem.LocMemCache` | No       |
| `CACHE_LOCATION` | Cache location/identifier  | `unique-snowflake`                              | No       |
| `SESSION_ENGINE` | Session backend            | `django.contrib.sessions.backends.db`           | No       |

### Example .env Files

#### Development (.env)

```env
# Core
SECRET_KEY=your-secret-key-here
DEBUG=True
TESTING=False

# Network
ALLOWED_HOSTS=localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
BACKEND_ORIGIN=http://localhost:8000

# Database (SQLite - no configuration needed for dev)
# Or use MySQL/PostgreSQL:
DB_PROFILE=local
DATABASE_URL_LOCAL=mysql://root:password@127.0.0.1:3306/mobileid_dev
```

#### Docker Development (.env.development)

```env
# Core
SECRET_KEY=dev-secret-key
DEBUG=True

# Network (use localhost for browser access)
ALLOWED_HOSTS=localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://localhost:5173

# Database (connect to host MySQL from container)
DB_PROFILE=local
DB_ENGINE=mysql
DB_HOST=host.docker.internal
DB_NAME=mobileid
DB_USER=root
DB_PASSWORD=rootpassword
```

#### Production (.env.production)

```env
# Core
SECRET_KEY=your-secure-random-secret-key
DEBUG=False
TESTING=False

# Network
ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
BACKEND_ORIGIN=https://api.yourdomain.com

# Cookies (HTTPS required)
COOKIE_SAMESITE=None
CSRF_COOKIE_SAMESITE=None
COOKIE_SECURE=True
CSRF_COOKIE_HTTPONLY=True
USE_HTTPS=True

# Database
DB_PROFILE=production
DATABASE_URL_LOCAL=postgres://user:password@db-host:5432/mobileid_prod
# Or for Cloud SQL:
# DATABASE_URL_GCP=postgres://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
DB_CONN_MAX_AGE=300
DB_SSL_MODE=require

# Security
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=30
```

## API Endpoints

### Authentication

- `POST /authn/login/` - User login
- `POST /authn/register/` - User registration
- `POST /authn/logout/` - User logout
- `GET /authn/user-info/` - Get current user information

### Barcode Management

- `GET /api/barcodes/` - List user barcodes
- `POST /api/barcodes/` - Create new barcode
- `GET /api/barcodes/{id}/` - Get barcode details
- `DELETE /api/barcodes/{id}/` - Delete barcode

### Dashboard (School Role)

- `GET /api/dashboard/` - Get dashboard statistics
- `GET /api/dashboard/barcodes/` - List all barcodes (admin view)

## User Roles

### User Role

- Create and manage personal barcodes
- Access basic profile features
- View personal barcode usage statistics

### School Role

- Access administrative dashboard
- View system-wide barcode analytics
- Manage multiple user barcodes
- Advanced barcode management features

## Security Features

- **JWT Authentication**: Secure token-based authentication with HTTP-only cookies
- **Rate Limiting**: API throttling to prevent abuse
- **CORS Protection**: Configured cross-origin resource sharing
- **CSRF Protection**: Cross-site request forgery prevention
- **Input Validation**: Comprehensive data validation and sanitization

## Deployment

### Production Checklist

1. Set `DEBUG=False` in environment variables
2. Configure a production database (PostgreSQL recommended)
3. Set up proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
4. Configure static file serving
5. Set up HTTPS with proper SSL certificates
6. Configure environment-specific secrets
7. Set up monitoring and logging

### Static Files

For production deployment:

```bash
cd src/
python manage.py collectstatic
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run linting and tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is proprietary software. All rights reserved.
