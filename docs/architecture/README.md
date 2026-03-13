# Architecture

MobileID is a dual-stack web application:

- **Backend**: Django REST API on AWS ECS (Fargate)
- **Frontend**: Vue.js SPA on AWS Amplify
- **Database**: MySQL/PostgreSQL on AWS RDS

## Authentication Flow

1. Frontend fetches RSA public key from `/authn/public-key/`
2. Password encrypted client-side with RSA before transmission
3. Backend decrypts and validates, issues JWT tokens as HttpOnly cookies
4. Browser sends cookies automatically on subsequent requests
5. Token refresh handled transparently via cookie-based refresh endpoint

## Key Design Decisions

- **Cookie-only auth**: JWT tokens stored exclusively in HttpOnly cookies (not localStorage) to mitigate XSS
- **WebAuthn/Passkeys**: Passwordless authentication supported as an alternative to password-based login
- **RSA password encryption**: Passwords encrypted in transit using rotating RSA key pairs
