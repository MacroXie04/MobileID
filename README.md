# Barcode Manager

A powerful full-stack barcode management application with barcode generation, user authentication, profile management, and more. Built with Django backend and Vue.js frontend.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Deployment Guide](#deployment-guide)
- [Contributing](#contributing)
- [License](#license)

## Features

### User Authentication
- **WebAuthn Support**: Modern biometric and hardware key authentication
- **Secure Login**: Brute force protection with login attempt limiting
- **Session Management**: Secure user session handling

### Barcode Management
- **Multiple Formats**: Support for PDF417, Code128, QR Code, and more
- **Batch Generation**: Create and manage barcodes in bulk
- **Barcode Preview**: Real-time preview of generated barcodes
- **Export Functionality**: Export barcode images

### User Management
- **Profile Management**: Users can edit and manage personal information
- **Settings Management**: Personalized application settings and preferences
- **Access Control**: Role-based access control

### Interface Design
- **Responsive Design**: Adapts to desktop and mobile devices
- **Theme Switching**: Support for multiple UI themes
- **Modern Interface**: Built with Bootstrap and Font Awesome icons

## Tech Stack

### Backend Technologies
- **[Django 4.x](https://www.djangoproject.com/)**: Powerful Python web framework
- **[Django REST Framework](https://www.django-rest-framework.org/)**: Building RESTful APIs
- **[Django-cors-headers](https://github.com/adamchainz/django-cors-headers)**: Handling CORS requests
- **[WebAuthn](https://pypi.org/project/webauthn/)**: Modern web authentication standard
- **[PostgreSQL](https://www.postgresql.org/)**: Enterprise-grade relational database

### Frontend Technologies
- **[Vue.js 3](https://vuejs.org/)**: Progressive JavaScript framework
- **[Vue Router](https://router.vuejs.org/)**: Official router for Vue.js
- **[Vite](https://vitejs.dev/)**: Next-generation frontend build tool
- **[Axios](https://axios-http.com/)**: HTTP client library
- **[Bootstrap 5](https://getbootstrap.com/)**: CSS framework
- **[Font Awesome](https://fontawesome.com/)**: Icon library

## Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 20.x or higher
- **PostgreSQL**: 12 or higher
- **Git**: For version control

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Barcode_Manager.git
   cd Barcode_Manager/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Create PostgreSQL database
   createdb barcode_manager
   
   # Copy environment configuration file
   cp .env.example .env
   # Edit .env file and update database connection details
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../GitHub_Pages
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

## Running the Application

### Start Backend Server

Run from the `backend` directory:

```bash
python manage.py runserver
```

Backend server will be running at `http://127.0.0.1:8000`

### Start Frontend Server

Run from the `GitHub_Pages` directory:

```bash
npm run dev
```

Frontend development server will be running at `http://localhost:5173`

### Production Build

```bash
npm run build
```

## Project Structure

```
Barcode_Manager/
├── backend/                 # Django backend
│   ├── barcode/            # Django project configuration
│   ├── mobileid/           # Main application
│   │   ├── api/            # API views
│   │   ├── forms/          # Form definitions
│   │   ├── models.py       # Data models
│   │   ├── serializers/    # API serializers
│   │   ├── static/         # Static files
│   │   ├── templates/      # HTML templates
│   │   └── views/          # View functions
│   └── requirements.txt    # Python dependencies
├── GitHub_Pages/           # Vue.js frontend
│   ├── src/
│   │   ├── views/          # Page components
│   │   ├── router/         # Route configuration
│   │   └── assets/         # Static assets
│   └── package.json        # Node.js dependencies
└── README.md              # Project documentation
```

## 📚 API Documentation

### Authentication API

#### User Registration
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

#### User Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

### Barcode API

#### Generate Barcode
```http
POST /api/barcode/generate/
Content-Type: application/json

{
  "content": "123456789",
  "format": "PDF417",
  "width": 300,
  "height": 100
}
```

#### Get Barcode List
```http
GET /api/barcode/list/
Authorization: Bearer <token>
```

### User API

#### Get User Profile
```http
GET /api/user/profile/
Authorization: Bearer <token>
```

#### Update User Profile
```http
PUT /api/user/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com"
}
```

## Testing

### Backend Testing

```bash
cd backend
pytest
```

### Frontend Testing

```bash
cd GitHub_Pages
npm run test
```

### Code Quality Checks

```bash
# Backend
cd backend
flake8 .
black .

# Frontend
cd GitHub_Pages
npm run lint
```

## Deployment Guide

### Frontend Deployment

The project is configured for automatic GitHub Pages deployment:

1. Push code to the `main` branch
2. GitHub Actions will automatically build and deploy to GitHub Pages
3. Access at `https://your-username.github.io/Barcode_Manager`

### Backend Deployment

Recommended deployment methods:

1. **Docker Deployment**
   ```bash
   docker build -t barcode-manager .
   docker run -p 8000:8000 barcode-manager
   ```

2. **Traditional Deployment**
   - Use Gunicorn as WSGI server
   - Configure Nginx as reverse proxy
   - Set environment variables and database connections

## Contributing

We welcome all forms of contributions!

### Contribution Process

1. **Fork the project**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Create a Pull Request**

### Development Standards

- Follow PEP 8 Python code standards
- Use ESLint for JavaScript code checking
- Write test cases for new features
- Update relevant documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact Us

- **Project Homepage**: [GitHub Repository](https://github.com/your-username/Barcode_Manager)
- **Issue Reports**: [Issues](https://github.com/your-username/Barcode_Manager/issues)
- **Feature Requests**: [Discussions](https://github.com/your-username/Barcode_Manager/discussions)

---

⭐ If this project helps you, please give us a star!

## Dockerized Local HTTPS Setup (WebAuthn/Passkeys)

This repository includes a multi-stage Dockerfile and a docker-compose setup that serve the Vue 3 SPA and the Django API behind a local HTTPS reverse proxy. This enables testing WebAuthn/Passkeys in a trusted HTTPS environment on `https://localhost`.

### Prerequisites
- Docker and Docker Compose
- [mkcert](https://github.com/FiloSottile/mkcert) (to create locally trusted TLS certificates)

### 1) Generate local certificates

```bash
brew install mkcert nss   # macOS (or see mkcert docs for your OS)
mkdir -p certs
mkcert -install
mkcert -key-file certs/localhost-key.pem -cert-file certs/localhost.pem localhost 127.0.0.1 ::1
```

This creates `./certs/localhost.pem` and `./certs/localhost-key.pem` used by the proxy.

### 2) Configure environment

Copy the example env and adjust as needed:

```bash
cp .env.example .env
```

Defaults use SQLite and enable HTTPS headers for local dev. Frontend builds with `VITE_API_BASE_URL=https://localhost/api`.

### 3) Build images

```bash
# Build both images via compose
VITE_API_BASE_URL=https://localhost/api docker compose build

# Or build individually
# Frontend image
docker build --target frontend-runtime -t mobileid-frontend:local .
# Backend image
docker build --target backend-runtime -t mobileid-backend:local .
```

### 4) Run the stack

```bash
docker compose up -d
```

- Reverse proxy: `https://localhost` (TLS via mkcert)
- Frontend: served by nginx (proxied at `/`)
- Backend API: proxied at `/api` → Django at `http://backend:8000`

### 5) Notes for WebAuthn/Passkeys
- The site is served over HTTPS at `https://localhost`, which is required for WebAuthn.
- The proxy sets `X-Forwarded-Proto: https`; ensure `USE_HTTPS=True` in `.env` so Django trusts proxy headers.
- If using Postgres, set `DB_ENGINE=django.db.backends.postgresql` and provide `DB_*` variables. Optionally start the `db` service in compose.

### Useful commands

```bash
# Tail logs
docker compose logs -f proxy backend frontend

# Rebuild after frontend changes
VITE_API_BASE_URL=https://localhost/api docker compose build frontend && docker compose up -d frontend

# Rebuild after backend changes
docker compose build backend && docker compose up -d backend
```