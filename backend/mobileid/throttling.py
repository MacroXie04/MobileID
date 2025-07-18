from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle for login endpoint to prevent brute force attacks.
    Limits anonymous users to 5 login attempts per minute.
    """

    scope = "login"


class RegistrationRateThrottle(AnonRateThrottle):
    """
    Throttle for registration endpoint to prevent abuse.
    Limits anonymous users to 5 registration attempts per day.
    """

    scope = "registration"


class BarcodeGenerationRateThrottle(UserRateThrottle):
    """
    Throttle for barcode generation endpoint.
    Limits authenticated users to 100 barcode generation requests per hour.
    """

    scope = "barcode_generation"


class BarcodeManagementRateThrottle(UserRateThrottle):
    """
    Throttle for barcode management endpoints (create, list, delete).
    Limits authenticated users to 50 barcode management requests per hour.
    """

    scope = "barcode_management"


class UserProfileRateThrottle(UserRateThrottle):
    """
    Throttle for user profile endpoints.
    Limits authenticated users to 20 profile update requests per hour.
    """

    scope = "user_profile"
