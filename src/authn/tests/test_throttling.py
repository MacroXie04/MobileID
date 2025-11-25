import copy

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from authn.throttling import (
    AdminLoginThrottle,
    LoginRateThrottle,
    UsernameRateThrottle,
)


class ThrottleFallbackTests(SimpleTestCase):
    """
    Ensure custom throttles keep working even if scopes are missing from settings.
    """

    def _rest_without_scope(self, scope):
        rest = copy.deepcopy(getattr(settings, "REST_FRAMEWORK", {}))
        rates = dict(rest.get("DEFAULT_THROTTLE_RATES", {}))
        rates.pop(scope, None)
        rest["DEFAULT_THROTTLE_RATES"] = rates
        return rest

    def test_login_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("login")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = LoginRateThrottle()
            self.assertEqual(throttle.get_rate(), LoginRateThrottle.fallback_rate)

    def test_username_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("login_username")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = UsernameRateThrottle()
            self.assertEqual(throttle.get_rate(), UsernameRateThrottle.fallback_rate)

    def test_admin_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("admin_login")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = AdminLoginThrottle()
            self.assertEqual(throttle.get_rate(), AdminLoginThrottle.fallback_rate)

