# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Django)
Run from the `src/` directory:
- **Development server**: `python manage.py runserver`
- **Database migrations**: `python manage.py makemigrations && python manage.py migrate`
- **Create superuser**: `python manage.py createsuperuser`
- **Collect static files**: `python manage.py collectstatic`
- **Django shell**: `python manage.py shell`

### Frontend (Vue.js)
Run from the `pages/` directory:
- **Development server**: `npm run dev` or `yarn dev`
- **Production build**: `npm run build` or `yarn build`
- **Preview build**: `npm run preview` or `yarn preview`
- **Lint**: `npm run lint` or `yarn lint`
- **Format**: `npm run format` or `yarn format`

## Project Architecture

### Dual-Stack Structure
This project uses a **dual-stack architecture** with separate backend and frontend codebases:
- **Backend**: Django REST API in `src/` directory
- **Frontend**: Vue.js SPA in `pages/` directory

### Backend Architecture (Django)
- **Main project**: `src/mobileid/` - Django settings and URL configuration
- **Authentication app**: `src/authn/` - User authentication, WebAuthn, JWT tokens
- **Index app**: `src/index/` - Barcode management and dashboard functionality
- **Database**: SQLite (default) with optional PostgreSQL/MySQL support

#### Key Django Apps:
1. **authn**: Handles user authentication, JWT tokens, WebAuthn, and user profiles
2. **index**: Manages barcodes, barcode generation, and dashboard functionality

#### Authentication System:
- Custom JWT authentication via cookies (`CookieJWTAuthentication`)
- WebAuthn support for passwordless authentication  
- User groups: "User" (basic) and "School" (admin) roles
- JWT tokens set to 10-year expiry for long-term sessions

### Frontend Architecture (Vue.js)
- **Framework**: Vue 3 with Composition API
- **Bundler**: Vite
- **UI Library**: Material Web Components (@material/web)
- **Styling**: CSS with Material Design 3 principles
- **Routing**: Vue Router with authentication guards

#### Key Frontend Structure:
- **Views**: Main page components (`views/home/`, `views/authn/`)
- **Components**: Reusable UI components organized by feature (`components/school/`, `components/user/`)
- **Composables**: Shared logic (`useApi.js`, `useUserInfo.js`, `usePdf417.js`)
- **API**: Backend communication layer (`api/auth.js`)

### Core Features
1. **Barcode Management**: PDF417 barcode generation and management
2. **User Authentication**: Login/register with WebAuthn support
3. **Role-based Access**: Different interfaces for School admins vs regular Users
4. **Dynamic Barcodes**: Server-side barcode generation with optional Selenium integration

### Configuration
- **Backend config**: Environment variables via `.env` file (see `settings.py` for options)
- **Frontend config**: Vite environment variables with `VITE_` prefix
- **CORS**: Configured for local development (ports 8080, 5173, 8000)

### Database Models
- **UserProfile**: Extended user information with avatars
- **Barcode**: Core barcode entity with UUID and type classification
- **BarcodeUsage**: Usage tracking and analytics
- **BarcodeUserProfile**: Barcode-specific user information
- **UserBarcodeSettings**: Per-user barcode configuration

### Development Workflow
1. Start Django backend: `cd src && python manage.py runserver`
2. Start Vue frontend: `cd pages && npm run dev`
3. Frontend runs on port 5173, backend on port 8000
4. Frontend communicates with backend via REST API

### Authentication Flow
1. Users register/login through Vue frontend
2. Backend issues JWT tokens stored in HTTP-only cookies
3. All API requests use cookie-based authentication
4. Vue router guards protect authenticated routes
5. Different user groups see different interfaces (Home vs Dashboard)

### Testing & Quality
- Frontend linting with ESLint and Prettier
- No test suite currently configured - check for any test files before assuming testing approach