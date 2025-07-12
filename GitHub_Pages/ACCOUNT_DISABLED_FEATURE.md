# Account Disabled Feature - Frontend Implementation

## Overview

This document describes the frontend implementation of the account disabled feature for the Vue.js application.

## Features

### 1. Account Disabled Page
- **Location**: `src/views/AccountDisabledView.vue`
- **Route**: `/account-disabled`
- **Purpose**: Displays a user-friendly message when a user's account is disabled

### 2. User Status Checking
- **Location**: `src/router/index.js`
- **Function**: Route guard that checks user status before allowing access to protected routes
- **Behavior**: Automatically redirects disabled users to the account disabled page

### 3. Registration Flow
- **Location**: `src/views/RegisterView.vue`
- **Behavior**: 
  - New users are registered with disabled status
  - No automatic login after registration
  - Shows success message indicating account needs activation

### 4. Login Flow
- **Location**: `src/views/LoginView.vue`
- **Behavior**: 
  - Checks user status after successful authentication
  - Redirects disabled users to account disabled page
  - Prevents disabled users from accessing the main application

## Implementation Details

### Route Guard Logic
```javascript
router.beforeEach(async (to, from, next) => {
    const loggedIn = localStorage.getItem('access_token');

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!loggedIn) {
            next({name: 'login'});
        } else {
            // Check if user is disabled (only for non-account-disabled routes)
            if (to.name !== 'account-disabled') {
                try {
                    // Check user status by making a request to the API
                    const response = await fetch('http://127.0.0.1:8000/me/', {
                        headers: {
                            'Authorization': `Bearer ${loggedIn}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.status === 401) {
                        // Token is invalid, redirect to login
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        next({name: 'login'});
                        return;
                    }
                    
                    if (response.ok) {
                        const userData = await response.json();
                        // Check if user is active
                        if (userData.is_active === false) {
                            next({name: 'account-disabled'});
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Error checking user status:', error);
                    // If there's an error checking user status, allow the request to proceed
                    // This prevents blocking users due to network issues
                }
            }
            next();
        }
    } else {
        next();
    }
});
```

### Account Disabled Page Features
- **Responsive Design**: Works on both desktop and mobile devices
- **User-Friendly Interface**: Clear messaging about account status
- **Logout Functionality**: Allows users to log out and return to login page
- **Professional Styling**: Consistent with the application's design system

### API Integration
- **User Status Check**: Uses `/me/` endpoint to verify user status
- **Error Handling**: Graceful handling of network errors and API failures
- **Token Management**: Proper cleanup of invalid tokens

## User Experience Flow

### For New Users
1. User registers with valid information
2. System creates account with disabled status
3. User sees success message about account activation requirement
4. User is redirected to login page
5. User cannot log in until account is activated by administrator

### For Disabled Users
1. User attempts to log in with valid credentials
2. System authenticates user but detects disabled status
3. User is automatically redirected to account disabled page
4. User sees clear message about account status
5. User can log out to return to login page

### For Active Users
1. User logs in with valid credentials
2. System checks user status and confirms account is active
3. User is redirected to main application
4. Normal application functionality is available

## Security Considerations

1. **Token Validation**: Invalid tokens are immediately cleared
2. **Status Verification**: User status is checked on every protected route access
3. **Graceful Degradation**: Network errors don't block legitimate users
4. **Clear Messaging**: Users understand why they can't access the system

## Error Handling

- **Network Errors**: Users are not blocked due to network issues
- **API Failures**: Graceful fallback to allow legitimate access
- **Invalid Tokens**: Automatic cleanup and redirect to login
- **Server Errors**: User-friendly error messages

## Styling and Design

The account disabled page follows the application's design system:
- **Bootstrap Integration**: Uses Bootstrap classes for consistent styling
- **Custom CSS**: Additional styling for enhanced visual appeal
- **Responsive Design**: Adapts to different screen sizes
- **Accessibility**: Proper semantic HTML and ARIA attributes

## Future Enhancements

1. **Real-time Status Updates**: WebSocket integration for immediate status changes
2. **Admin Contact Information**: Display contact details for account activation
3. **Status History**: Show when and why account was disabled
4. **Reactivation Requests**: Allow users to request account reactivation 