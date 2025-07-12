# Environment Variable Configuration Guide

## Overview

This project uses environment variables to configure Django settings. For security reasons, sensitive information (such as SECRET_KEY) should be provided through environment variables rather than hardcoded in the code.

## Quick Start

1. Create a `.env` file in the `backend/` directory
2. Copy the following content to the `.env` file:

```bash
# Django Settings
# Generate new key: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-secret-key-here

# Development environment settings (set to False for production)
DEBUG=True

# Project API and Web application modes
# When API_SERVER is enabled, Django only provides API endpoints
API_SERVER=False
API_ENABLED=True
WEBAPP_ENABLED=True

# Enable Django default web admin interface
WEB_ADMIN=True
USER_REGISTRATION_ENABLED=True

# Enable Selenium web scraping
SELENIUM_ENABLED=False
```

## Environment Variable Descriptions

### Required Variables

- `SECRET_KEY`: Django secret key used for encrypting sessions, etc. **Must set a strong key in production environment**

### Optional Variables (with default values)

- `DEBUG`: Debug mode (default: True)
- `API_SERVER`: API-only server mode (default: False)
- `API_ENABLED`: Enable API functionality (default: True)
- `WEBAPP_ENABLED`: Enable web application functionality (default: True)
- `WEB_ADMIN`: Enable Django admin interface (default: True)
- `USER_REGISTRATION_ENABLED`: Enable user registration (default: True)
- `SELENIUM_ENABLED`: Enable Selenium functionality (default: False)

## Production Environment Configuration

In production environments, it's recommended to use the following settings:

```bash
# Production environment settings
SECRET_KEY=your-production-secret-key
DEBUG=False
API_SERVER=True
WEBAPP_ENABLED=False
WEB_ADMIN=False
USER_REGISTRATION_ENABLED=False
SELENIUM_ENABLED=False
```

## Generating SECRET_KEY

Run the following command to generate a new SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Important Notes

1. The `.env` file has been added to `.gitignore` and will not be committed to version control
2. In development environment, if `SECRET_KEY` is not set, a default development key will be used
3. In production environment, a strong key must be set
4. All boolean environment variables accept 'true'/'false' strings (case-insensitive) 