from django.utils.encoding import force_str
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    """
    Scoped throttle for overall login attempts per client/IP.
    """

    scope = "login"


class UsernameRateThrottle(SimpleRateThrottle):
    """
    Throttle login attempts per username to limit credential stuffing.
    """

    scope = "login_username"

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

