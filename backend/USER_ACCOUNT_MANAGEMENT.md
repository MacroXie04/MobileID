# User Account Management Feature

## Overview

This system implements user account disabling functionality. Newly registered users are disabled by default and require administrator activation before they can use the system.

## Features

### 1. New User Registration
- Newly registered users are disabled by default (`is_active=False`)
- No automatic login after registration
- API registration does not return access tokens

### 2. User Status Checking
- Disabled users cannot log into the system
- Logged-in but disabled users are redirected to the "Account Disabled" page
- Disabled users cannot access any protected pages

### 3. Account Disabled Page
- Beautiful disabled status notification page
- Provides logout option
- Includes contact administrator information

## Management Commands

### Activate User Account
```bash
python manage.py activate_user <username>
```

### Disable User Account
```bash
python manage.py deactivate_user <username>
```

### List All Disabled Users
```bash
# Simple list
python manage.py list_disabled_users

# Detailed information
python manage.py list_disabled_users --verbose
```

## Middleware

The system uses `UserStatusMiddleware` to check user status:

- **Location**: `mobileid.middleware.UserStatusMiddleware`
- **Function**: Checks logged-in user status, redirects disabled users to account disabled page
- **Excluded URLs**: `/logout/`, `/admin/`, `/account-disabled/`

## Database Fields

Uses Django's built-in User model `is_active` field:
- `is_active=True`: User account is normal
- `is_active=False`: User account is disabled

## Security Considerations

1. **New Users Default Disabled**: Prevents malicious registration
2. **Login Check**: Disabled users cannot log in
3. **Page Access Control**: Disabled users cannot access system features
4. **Middleware Protection**: Global user status checking

## Usage Flow

### User Registration Flow
1. User fills out registration information
2. System creates user account (`is_active=False`)
3. Displays registration success message, prompts for administrator activation
4. User cannot log in until account is activated

### Administrator Activation Flow
1. Administrator uses management commands to view disabled users
2. Uses activation command to activate specified user
3. User can now log in and use the system normally

### Disable User Flow
1. Administrator uses disable command to disable specified user
2. User is redirected to disabled page on next access
3. User cannot access any system features

## Notes

1. Administrator accounts should not be disabled
2. Recommend regular checking of disabled user list
3. User status can be managed through Django admin interface
4. API users also follow the same disable rules 