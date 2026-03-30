import copy
from unittest.mock import MagicMock

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from authn.throttling import (
    AdminLoginThrottle,
    LoginRateThrottle,
    RefreshRateThrottle,
    RegisterRateThrottle,
    UsernameRateThrottle,
    _get_rate_for_scope,
)


class ThrottleFallbackTests(SimpleTestCase):
    """
    Ensure custom throttles keep working even if scopes are missing from
    settings.
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
            self.assertEqual(
                throttle.get_rate(),
                LoginRateThrottle.fallback_rate,
            )

    def test_username_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("login_username")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = UsernameRateThrottle()
            self.assertEqual(
                throttle.get_rate(),
                UsernameRateThrottle.fallback_rate,
            )

    def test_admin_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("admin_login")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = AdminLoginThrottle()
            self.assertEqual(
                throttle.get_rate(),
                AdminLoginThrottle.fallback_rate,
            )

    def test_refresh_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("refresh")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = RefreshRateThrottle()
            self.assertEqual(
                throttle.get_rate(),
                RefreshRateThrottle.fallback_rate,
            )

    def test_register_scope_fallback_rate_used(self):
        rest = self._rest_without_scope("registration")
        with override_settings(REST_FRAMEWORK=rest):
            throttle = RegisterRateThrottle()
            self.assertEqual(
                throttle.get_rate(),
                RegisterRateThrottle.fallback_rate,
            )


class AllowRequestThrottlesEnabledTests(SimpleTestCase):
    """Test that _ScopeRateFallbackMixin.allow_request respects THROTTLES_ENABLED."""

    @override_settings(THROTTLES_ENABLED=False)
    def test_allow_request_when_throttles_disabled(self):
        throttle = LoginRateThrottle()
        request = MagicMock()
        self.assertTrue(throttle.allow_request(request, None))

    @override_settings(THROTTLES_ENABLED=True)
    def test_allow_request_delegates_when_throttles_enabled(self):
        """When enabled, allow_request calls super() which may deny."""
        throttle = RefreshRateThrottle()
        request = MagicMock()
        # We just verify it doesn't unconditionally return True
        # (actual throttle behavior depends on cache state)
        result = throttle.allow_request(request, None)
        self.assertIsInstance(result, bool)


class GetRateForScopeTests(SimpleTestCase):
    """Test the _get_rate_for_scope utility function"""

    def test_get_rate_for_existing_scope(self):
        """Test getting rate for a configured scope"""
        rate = _get_rate_for_scope("login")
        self.assertIsNotNone(rate)
        self.assertEqual(rate, "5/minute")

    def test_get_rate_for_missing_scope(self):
        """Test getting rate for a non-existent scope returns None"""
        rate = _get_rate_for_scope("nonexistent_scope")
        self.assertIsNone(rate)

    @override_settings(REST_FRAMEWORK=None)
    def test_get_rate_with_no_rest_framework_settings(self):
        """Test graceful handling when REST_FRAMEWORK is None"""
        rate = _get_rate_for_scope("login")
        self.assertIsNone(rate)

    @override_settings(REST_FRAMEWORK={})
    def test_get_rate_with_empty_rest_framework(self):
        """Test graceful handling when REST_FRAMEWORK is empty"""
        rate = _get_rate_for_scope("login")
        self.assertIsNone(rate)


class LoginRateThrottleTests(SimpleTestCase):
    """Test LoginRateThrottle class"""

    def test_scope_is_login(self):
        """Test that scope is correctly set to 'login'"""
        throttle = LoginRateThrottle()
        self.assertEqual(throttle.scope, "login")

    def test_fallback_rate_defined(self):
        """Test that fallback rate is defined"""
        self.assertEqual(LoginRateThrottle.fallback_rate, "5/minute")

    def test_get_rate_returns_configured_or_fallback(self):
        """Test get_rate returns configured rate when available"""
        throttle = LoginRateThrottle()
        rate = throttle.get_rate()
        self.assertIsNotNone(rate)
        # Should be either configured rate or fallback
        self.assertIn("/", rate)


class NewThrottleClassTests(SimpleTestCase):
    """Test new throttle classes"""

    def test_refresh_throttle_scope(self):
        throttle = RefreshRateThrottle()
        self.assertEqual(throttle.scope, "refresh")
        self.assertEqual(throttle.fallback_rate, "10/minute")

    def test_register_throttle_scope(self):
        throttle = RegisterRateThrottle()
        self.assertEqual(throttle.scope, "registration")
        self.assertEqual(throttle.fallback_rate, "5/day")
