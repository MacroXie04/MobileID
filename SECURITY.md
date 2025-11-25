# Security Policy

## Supported Versions

We currently support the following versions of MobileID with security updates:

| Version            | Supported          |
| ------------------ | ------------------ |
| Latest Main Branch | :white_check_mark: |
| < 1.0.0            | :x:                |

## Reporting a Vulnerability

We take the security of MobileID seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Do not open public GitHub issues for security vulnerabilities.**

Please report security vulnerabilities by emailing the project maintainers or by opening a draft Security Advisory in the GitHub repository if you have access.

In your report, please include:

1.  The type of vulnerability (e.g., SQL injection, XSS, etc.).
2.  Full paths to the source file(s) related to the vulnerability.
3.  Steps to reproduce the vulnerability.
4.  Any special configuration required to reproduce the issue.

### Response Timeline

We are committed to addressing security vulnerabilities promptly:

- **Acknowledgment**: We will acknowledge your report within 48 hours.
- **Assessment**: We will assess the severity and impact of the vulnerability within 1 week.
- **Fix**: We will aim to provide a fix or mitigation within 2 weeks for critical issues.

### Security Features

MobileID implements several security features to protect user data:

- **RSA Encryption**: Passwords are encrypted on the client side using RSA before transmission.
- **WebAuthn**: Support for FIDO2/WebAuthn for secure, passwordless authentication.
- **JWT Authentication**: Secure, HTTP-only cookies are used for session management.
- **CSRF Protection**: All state-changing requests are protected against Cross-Site Request Forgery.
- **Content Security Policy**: Strict CSP headers are implemented to prevent XSS attacks.

Please review `CLAUDE.md` and the codebase for implementation details of these security features.
