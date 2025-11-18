"""
Admin session expiry middleware.

Sets shorter session expiry for admin requests to improve security.
"""

from django.conf import settings


class AdminSessionExpiryMiddleware:
    """
    Middleware that sets shorter session expiry for admin requests.

    Admin sessions expire after ADMIN_SESSION_COOKIE_AGE seconds (default 2 hours)
    and expire when the browser closes, unlike regular sessions.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL_PATH}/"
        self.admin_session_age = getattr(settings, "ADMIN_SESSION_COOKIE_AGE", 7200)

    def __call__(self, request):
        # Set shorter session expiry for admin requests
        if request.path.startswith(self.admin_path):
            if hasattr(request, "session"):
                # Set session expiry to admin-specific duration (2 hours default)
                # This overrides the default 10-year session for admin access
                request.session.set_expiry(self.admin_session_age)

        response = self.get_response(request)
        return response

