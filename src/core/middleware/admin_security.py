"""
Admin security middleware: availability, IP whitelist, session expiry, and login
throttling.
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden


def _get_client_ip(request):
    """Extract client IP from request, handling proxy headers."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class AdminIPWhitelistMiddleware:
    """
    Restricts admin access to whitelisted IP addresses.

    Only applies when ADMIN_ALLOWED_IPS is configured (non-empty list).
    If ADMIN_ALLOWED_IPS is empty, allows all access (for development).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL_PATH}/"
        self.allowed_ips = set(getattr(settings, "ADMIN_ALLOWED_IPS", []))

    def __call__(self, request):
        if self.allowed_ips and request.path.startswith(self.admin_path):
            client_ip = _get_client_ip(request)
            if client_ip not in self.allowed_ips:
                return HttpResponseForbidden(
                    "Access denied. Your IP address is not authorized to "
                    "access this resource."
                )

        return self.get_response(request)


class AdminAvailabilityMiddleware:
    """
    Short-circuit Django admin in DynamoDB-only deployments.

    The current production DynamoDB-only topology does not provision the
    relational database tables required by Django's built-in admin, auth, and
    session stack. Returning an explicit 503 avoids opaque 500s from session
    writes or ORM access.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL_PATH}/"

    def __call__(self, request):
        if getattr(
            settings, "PERSISTENCE_MODE", "hybrid"
        ) == "dynamodb" and request.path.startswith(self.admin_path):
            response = HttpResponse(
                (
                    "Django admin is unavailable in DynamoDB-only deployments. "
                    "This environment does not provision the relational auth and "
                    "session tables required by the built-in admin."
                ),
                status=503,
                content_type="text/plain; charset=utf-8",
            )
            response["Cache-Control"] = "no-store"
            return response

        return self.get_response(request)


class AdminSessionExpiryMiddleware:
    """
    Sets shorter session expiry for admin requests.

    Admin sessions expire after ADMIN_SESSION_COOKIE_AGE seconds (default 2 hours)
    and expire when the browser closes, unlike regular sessions.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL_PATH}/"
        self.admin_session_age = getattr(settings, "ADMIN_SESSION_COOKIE_AGE", 7200)

    def __call__(self, request):
        if request.path.startswith(self.admin_path):
            if hasattr(request, "session"):
                request.session.set_expiry(self.admin_session_age)

        response = self.get_response(request)
        return response


class AdminLoginThrottleMiddleware:
    """
    Applies rate limiting to admin login POST requests to prevent brute
    force attacks. Uses Django's cache framework to track attempts per IP.
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
        if request.method == "POST" and request.path == self.admin_login_path:
            if self._is_throttled(request):
                return HttpResponse(
                    "Too many login attempts. Please try again later.",
                    status=429,
                )

        return self.get_response(request)

    def _is_throttled(self, request):
        client_ip = _get_client_ip(request)
        if not client_ip:
            return False

        num_requests, duration = self._parse_rate(self.rate)
        if not num_requests or not duration:
            return False

        cache_key = f"admin_login_throttle_{client_ip}"
        count = cache.get(cache_key, 0)

        if count >= num_requests:
            return True

        cache.set(cache_key, count + 1, duration)
        return False

    def _parse_rate(self, rate):
        """Parse rate string like "5/15min" into (num_requests, duration_seconds)."""
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
