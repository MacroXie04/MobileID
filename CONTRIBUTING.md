# Contributing to MobileID

Thank you for your interest in contributing to MobileID! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style Guidelines](#code-style-guidelines)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [CI/CD Pipeline](#cicd-pipeline)

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- **Python 3.12+** (for backend development)
- **Node.js 18+** (for frontend development)
- **Docker Desktop** (optional, for containerized development)
- **Yarn** (preferred package manager for frontend)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/MobileID.git
   cd MobileID
   ```
3. Add the upstream repository as a remote:
   ```bash
   git remote add upstream https://github.com/<original-owner>/MobileID.git
   ```

## Development Setup

### Backend Setup

```bash
# Navigate to the source directory and create a virtual environment
cd src/
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp ../.env.example .env  # Adjust as needed

# Run database migrations
cd ..
python manage.py migrate

# Start the development server
python manage.py runserver
```

The Django API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
cd pages/

# Install dependencies (Yarn is preferred)
yarn install
# or: npm install

# Start the development server
yarn dev
```

The Vue.js application will be available at `http://localhost:5173`.

### Docker Setup (Alternative)

```bash
# Create environment file
cp .env.example .env.development

# Start the containerized API
docker compose up --build
```

## Project Structure

```
MobileID/
├── src/                    # Django backend
│   ├── authn/              # Authentication app (WebAuthn, JWT, user profiles)
│   ├── core/               # Core Django settings and configuration
│   ├── index/              # Barcode management app
│   └── requirements.txt    # Python dependencies
├── pages/                  # Vue.js frontend
│   ├── src/
│   │   ├── app/            # App configuration, router, main entry
│   │   ├── features/       # Feature modules (auth, dashboard, home, etc.)
│   │   ├── shared/         # Shared components, composables, utilities
│   │   └── assets/         # Static assets and styles
│   ├── tests/              # Unit and E2E tests
│   └── package.json        # Node.js dependencies
└── .github/workflows/      # CI/CD pipeline configurations
```

## Code Style Guidelines

This project enforces code style through automated CI checks. All contributions must pass these checks before merging.

### Backend (Python)

We use three complementary linting tools:

| Tool   | Purpose                 | Command           |
| ------ | ----------------------- | ----------------- |
| Black  | Code formatting         | `black --check .` |
| Ruff   | Fast linting            | `ruff check .`    |
| Flake8 | Additional style checks | `flake8 .`        |

**Before committing backend changes:**

```bash
cd src/

# Format code with Black
black .

# Check for linting issues
ruff check .
flake8 .
```

### Frontend (JavaScript/Vue)

| Tool     | Purpose         | Command       |
| -------- | --------------- | ------------- |
| ESLint   | Linting         | `yarn lint`   |
| Prettier | Code formatting | `yarn format` |

**Before committing frontend changes:**

```bash
cd pages/

# Format code with Prettier
yarn format

# Check for linting errors
yarn lint
```

### General Guidelines

- Write clear, self-documenting code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and concise
- Follow existing patterns in the codebase

## Making Changes

### Branching Strategy

1. Create a new branch from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. Use descriptive branch names:
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `docs/` - Documentation updates
   - `refactor/` - Code refactoring

### Commit Messages

Write clear, concise commit messages:

- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 72 characters
- Reference issue numbers when applicable

Example:

```
Add WebAuthn credential validation

- Implement server-side credential verification
- Add error handling for invalid credentials
- Update tests for new validation logic

Fixes #123
```

## Testing

### Backend Tests

```bash
cd src/

# Run all Django tests
python manage.py test

# Run tests with coverage
python -m coverage run manage.py test
python -m coverage report
```

### Frontend Tests

```bash
cd pages/

# Run unit tests
yarn test:unit

# Run unit tests in watch mode
yarn test

# Run E2E tests (requires Playwright browsers)
npx playwright install --with-deps
yarn test:e2e
```

### Test Guidelines

- Write tests for new features and bug fixes
- Maintain or improve existing test coverage
- Test edge cases and error conditions
- Keep tests focused and independent

## Submitting a Pull Request

1. **Ensure all checks pass locally:**

   ```bash
   # Backend
   cd src/ && black . && ruff check . && flake8 . && python manage.py test

   # Frontend
   cd pages/ && yarn format && yarn lint && yarn test:unit
   ```

2. **Push your branch:**

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request:**

   - Go to the repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template with:
     - Description of changes
     - Related issue numbers
     - Testing performed
     - Screenshots (for UI changes)

4. **Respond to feedback:**
   - Address reviewer comments promptly
   - Push additional commits to your branch
   - Re-request review when ready

## CI/CD Pipeline

All pull requests trigger automated checks:

### Backend Pipeline

1. **Lint Ruff** - Fast Python linting
2. **Lint Black** - Code formatting check
3. **Lint Flake8** - Additional style checks
4. **Django Tests** - Unit tests with coverage
5. **Database Migrations** - Migration consistency check

### Frontend Pipeline

1. **Lint ESLint** - JavaScript/Vue linting
2. **Lint Prettier** - Code formatting check
3. **Unit Tests** - Vitest unit tests
4. **E2E Tests** - Playwright browser tests

### Additional Checks

- **CodeQL** - Security analysis
- **Security Scan** - Vulnerability scanning
- **Docker Build** - Container build verification

All checks must pass before a PR can be merged to `main`.

## Security

If you discover a security vulnerability, please **do not** open a public issue. Instead, follow the guidelines in [SECURITY.md](SECURITY.md).

## Questions?

If you have questions about contributing, feel free to:

- Open a discussion on GitHub
- Review existing issues and pull requests
- Check the [README.md](README.md) for project documentation

Thank you for contributing to MobileID!

