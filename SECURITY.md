# Security Policy

## Supported Versions

We actively provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Security Features

MobileID implements several security measures:

### Authentication & Authorization
- **JWT Token Authentication**: HTTP-only cookies with 10-year expiry
- **WebAuthn Support**: Passwordless authentication using biometrics/security keys
- **Role-based Access Control**: User and School admin roles with different permissions
- **Custom Authentication Backend**: `CookieJWTAuthentication` for secure API access

### Data Protection
- **Barcode Security**: UUID-based barcode identification to prevent enumeration
- **User Data Isolation**: Barcode-specific user profiles prevent data leakage
- **Database Security**: Parameterized queries to prevent SQL injection
- **Static File Protection**: Proper static file handling with Django's security settings

### Network Security
- **CORS Configuration**: Properly configured for development and production environments
- **HTTPS Ready**: Designed to work with HTTPS in production
- **API Security**: RESTful API with authentication required for sensitive operations

## Security Best Practices

When contributing to MobileID:

1. **Never commit secrets**: Use environment variables for sensitive configuration
2. **Validate input**: Always validate and sanitize user input on both frontend and backend
3. **Use parameterized queries**: Avoid string concatenation in database queries
4. **Keep dependencies updated**: Regularly update Python and npm dependencies
5. **Follow authentication flows**: Use the established JWT/WebAuthn patterns

## Reporting a Vulnerability

If you discover a security vulnerability in MobileID, please report it responsibly:

### How to Report
1. **Email**: Send details to the project maintainers via GitHub
2. **GitHub Issues**: For non-critical issues, create a private security advisory
3. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Timeline**: Varies based on severity (critical issues prioritized)
- **Disclosure**: Coordinated disclosure after fix is available

### What to Expect
- **Accepted vulnerabilities**: We'll work on a fix and credit you in the security advisory
- **Declined reports**: We'll explain why the issue doesn't qualify as a security vulnerability
- **Critical issues**: May result in immediate patches and security releases

## Security Considerations for Deployment

### Production Environment
- Use HTTPS for all connections
- Configure proper CORS settings for your domain
- Set secure cookie flags in Django settings
- Use a production-ready database (PostgreSQL/MySQL)
- Enable Django's security middleware
- Keep static files properly secured

### Environment Variables
Secure the following sensitive configuration:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database connection string
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Restrict to your domain(s)

### Regular Maintenance
- Update dependencies monthly
- Monitor for security advisories
- Review user access and permissions quarterly
- Backup databases regularly with encryption
