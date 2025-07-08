# Rate Limiting in Django REST Framework

This document explains the rate limiting implementation in the Barcode Manager application.

## Overview

Rate limiting has been added to the Django REST Framework API endpoints to prevent abuse and ensure fair usage of the system. Different endpoints have different rate limits based on their sensitivity and expected usage patterns.

## Configuration

Rate limiting is configured in `backend/barcode/settings.py` with the following settings:

```python
REST_FRAMEWORK = {
    # ... other settings ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'login': '5/minute',
        'registration': '5/day',
        'barcode_generation': '100/hour',
        'barcode_management': '50/hour',
        'user_profile': '20/hour',
    },
}
```

## Custom Throttle Classes

Custom throttle classes are defined in `backend/mobileid/throttling.py`:

1. `LoginRateThrottle` - Limits anonymous users to 5 login attempts per minute
2. `RegistrationRateThrottle` - Limits anonymous users to 5 registration attempts per day
3. `BarcodeGenerationRateThrottle` - Limits authenticated users to 100 barcode generation requests per hour
4. `BarcodeManagementRateThrottle` - Limits authenticated users to 50 barcode management requests per hour
5. `UserProfileRateThrottle` - Limits authenticated users to 20 profile update requests per hour

## Applied Rate Limits

The following API endpoints have rate limiting applied:

1. Login endpoint (`ThrottledTokenObtainPairView`) - Limited to 5 requests per minute per IP address
2. Registration endpoint (`RegisterAPIView`) - Limited to 5 requests per day per IP address
3. Barcode generation endpoint (`GenerateBarcodeView`) - Limited to 100 requests per hour per user
4. Barcode management endpoints (`BarcodeListCreateAPIView`, `BarcodeDestroyAPIView`) - Limited to 50 requests per hour per user
5. User profile endpoints (`UserProfileAPIView`, `BarcodeSettingsAPIView`) - Limited to 20 requests per hour per user

## Testing Rate Limiting

To test rate limiting, you can use tools like `curl` or Postman to make repeated requests to the API endpoints. When the rate limit is exceeded, the server will respond with a 429 Too Many Requests status code and a message indicating when the rate limit will reset.

Example response when rate limit is exceeded:
```json
{
    "detail": "Request was throttled. Expected available in 35 seconds."
}
```

## Monitoring and Adjusting Rate Limits

The rate limits can be adjusted in the `settings.py` file based on the application's needs. Monitor the API usage patterns and adjust the limits accordingly to balance between preventing abuse and ensuring a good user experience.
