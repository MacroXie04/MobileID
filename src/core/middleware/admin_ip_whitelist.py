"""
Admin IP whitelist middleware.

Blocks access to admin URLs unless the client IP is in the allowed list.
"""

from django.conf import settings
from django.http import HttpResponseForbidden


class AdminIPWhitelistMiddleware:
    """
    Middleware that restricts admin access to whitelisted IP addresses.

    Only applies when ADMIN_ALLOWED_IPS is configured (non-empty list).
    If ADMIN_ALLOWED_IPS is empty, the middleware allows all access (for development).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL_PATH}/"
        self.allowed_ips = set(getattr(settings, "ADMIN_ALLOWED_IPS", []))

    def __call__(self, request):
        # Only check if IP whitelist is configured
        if self.allowed_ips and request.path.startswith(self.admin_path):
            client_ip = self._get_client_ip(request)
            if client_ip not in self.allowed_ips:
                return HttpResponseForbidden(
                    "Access denied. Your IP address is not authorized to access this resource."
                )

        return self.get_response(request)

    def _get_client_ip(self, request):
        """
        Extract client IP from request, handling proxy headers.

        Checks X-Forwarded-For header first (for reverse proxies),
        then falls back to REMOTE_ADDR.
        """
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
