# MobileID

A secure, dual-stack web application for mobile identification and barcode management built with Django and Vue.js.

## Overview

MobileID provides a comprehensive platform for generating, managing, and authenticating PDF417 barcodes with role-based access control. 

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
- Node.js 16+
- npm or yarn

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
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser
```

### 3. Frontend Setup
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
The Django API will be available at `http://127.0.0.1:8000`

#### Frontend Server
```bash
cd pages/
npm run dev
# or
yarn dev
```
The Vue.js application will be available at `http://127.0.0.1:5173`

### Code Quality

#### Frontend Linting and Formatting
```bash
cd pages/
npm run lint        # Check for linting errors
npm run format      # Format code with Prettier
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Key variables include:

- `SECRET_KEY`: Django secret key for cryptographic operations
- `DEBUG`: Enable/disable debug mode
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `CORS_ALLOWED_ORIGINS`: Frontend URLs for CORS configuration
- `DATABASE_URL`: Database connection string (optional)
- `SELENIUM_ENABLED`: Enable dynamic barcode generation features

### Database Configuration

By default, the application uses SQLite for development. For production, configure PostgreSQL or MySQL via environment variables:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mobileid
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
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

## Support

For technical support and questions, please contact the development team or open an issue in the project repository.