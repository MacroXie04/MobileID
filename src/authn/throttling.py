from django.conf import settings
from django.utils.encoding import force_str
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


def _get_rate_for_scope(scope: str):
    """
    Return the configured throttle rate for a given scope, if any.
    """

    rest_framework_cfg = getattr(settings, "REST_FRAMEWORK", {}) or {}
    rates = rest_framework_cfg.get("DEFAULT_THROTTLE_RATES") or {}
    return rates.get(scope)


class _ScopeRateFallbackMixin:
    """
    Provide a resilient get_rate implementation that falls back to defaults.

    DRF raises ImproperlyConfigured if a scope is missing from
    DEFAULT_THROTTLE_RATES. This mixin lets project-specific throttles keep
    working even if downstream settings overrides accidentally remove a scope.
    """

    fallback_rate: str | None = None

    def get_rate(self):
        configured = _get_rate_for_scope(getattr(self, "scope", None))
        if configured:
            return configured
        return self.fallback_rate


class LoginRateThrottle(_ScopeRateFallbackMixin, ScopedRateThrottle):
    """
    Scoped throttle for overall login attempts per client/IP.
    """

    scope = "login"
    fallback_rate = "5/minute"


class UsernameRateThrottle(_ScopeRateFallbackMixin, SimpleRateThrottle):
    """
    Throttle login attempts per username to limit credential stuffing.
    """

    scope = "login_username"
    fallback_rate = "5/minute"

    def get_cache_key(self, request, view):
        if request.method != "POST":
            return None

        username = self._extract_username(request)
        if not username:
            return None

        ident = force_str(username).lower()
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def parse_rate(self, rate):
        if rate and rate.endswith("15min"):
            num_requests = rate.split("/", 1)[0]
            try:
                num_requests = int(num_requests)
            except ValueError:
                return None, None
            return num_requests, 15 * 60
        return super().parse_rate(rate)

    @staticmethod
    def _extract_username(request):
        data = getattr(request, "data", {}) or {}
        return data.get("username") or data.get("email")


class AdminLoginThrottle(_ScopeRateFallbackMixin, SimpleRateThrottle):
    """
    Throttle admin login attempts per client/IP.

    This throttle is applied via middleware to Django admin login POST
    requests.
    """

    scope = "admin_login"
    fallback_rate = "5/15min"

    def get_cache_key(self, request, view):
        """
        Generate cache key based on client IP for admin login throttling.
        """
        if request.method != "POST":
            return None

        # Only apply to admin login URLs
        if not request.path.endswith("/admin/login/"):
            return None

        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def parse_rate(self, rate):
        """
        Parse rate string like "5/15min" into (num_requests, duration).
        """
        if rate and rate.endswith("15min"):
            num_requests = rate.split("/", 1)[0]
            try:
                num_requests = int(num_requests)
            except ValueError:
                return None, None
            return num_requests, 15 * 60
        return super().parse_rate(rate)
