"""
 login throttling middleware.

Applies rate limiting to Django  login POST requests to prevent brute
force attacks.
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


class AdminLoginThrottleMiddleware:
    """
    Middleware that applies rate limiting to admin login attempts.

    Uses Django's cache framework to track login attempts per IP address.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_url_path = getattr(settings, "ADMIN_URL_PATH", "admin")
        self.admin_login_path = f"/{self.admin_url_path}/login/"
        self.rate = (
            getattr(settings, "REST_FRAMEWORK", {})
            .get("DEFAULT_THROTTLE_RATES", {})
            .get("admin_login", "5/15min")
        )

    def __call__(self, request):
        # Only check POST requests to admin login
        if request.method == "POST" and request.path == self.admin_login_path:
            if self._is_throttled(request):
                return HttpResponse(
                    "Too many login attempts. Please try again later.",
                    status=429,
                )

        return self.get_response(request)

    def _is_throttled(self, request):
        """
        Check if the request should be throttled based on IP address.

        Returns True if throttled, False otherwise.
        """
        client_ip = self._get_client_ip(request)
        if not client_ip:
            return False

        # Parse rate: "5/15min" -> (5, 900)
        num_requests, duration = self._parse_rate(self.rate)
        if not num_requests or not duration:
            return False

        # Generate cache key
        cache_key = f"admin_login_throttle_{client_ip}"

        # Get current count
        count = cache.get(cache_key, 0)

        if count >= num_requests:
            return True

        # Increment count
        cache.set(cache_key, count + 1, duration)
        return False

    def _parse_rate(self, rate):
        """
        Parse rate string like "5/15min" into (num_requests, duration_seconds).

        Returns (None, None) if parsing fails.
        """
        if not rate:
            return None, None

        try:
            if rate.endswith("15min"):
                num_requests = int(rate.split("/", 1)[0])
                return num_requests, 15 * 60
            elif "/" in rate:
                parts = rate.split("/")
                num_requests = int(parts[0])
                time_unit = parts[1]

                if time_unit.endswith("min"):
                    duration = int(time_unit[:-3]) * 60
                elif time_unit.endswith("hour"):
                    duration = int(time_unit[:-4]) * 3600
                elif time_unit.endswith("day"):
                    duration = int(time_unit[:-3]) * 86400
                else:
                    duration = int(time_unit)

                return num_requests, duration
        except (ValueError, IndexError):
            pass

        return None, None

    def _get_client_ip(self, request):
        """
        Extract client IP from request, handling proxy headers.
        """
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
