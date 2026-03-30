from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase

from authn.throttling import (
    AdminLoginThrottle,
    UsernameRateThrottle,
)


class UsernameRateThrottleTests(TestCase):
    """Test UsernameRateThrottle class"""

    def test_scope_is_login_username(self):
        """Test that scope is correctly set"""
        throttle = UsernameRateThrottle()
        self.assertEqual(throttle.scope, "login_username")

    def test_fallback_rate_defined(self):
        """Test that fallback rate is defined"""
        self.assertEqual(UsernameRateThrottle.fallback_rate, "5/minute")

    def test_get_cache_key_returns_none_for_get_request(self):
        """Test that GET requests don't get throttled"""
        throttle = UsernameRateThrottle()
        request = MagicMock()
        request.method = "GET"

        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNone(cache_key)

    def test_get_cache_key_returns_none_without_username(self):
        """Test that requests without username don't get throttled"""
        throttle = UsernameRateThrottle()
        request = MagicMock()
        request.method = "POST"
        request.data = {}

        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNone(cache_key)

    def test_get_cache_key_uses_username(self):
        """Test that cache key is based on username"""
        throttle = UsernameRateThrottle()
        request = MagicMock()
        request.method = "POST"
        request.data = {"username": "TestUser"}

        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
        # Username should be lowercased in cache key
        self.assertIn("testuser", cache_key.lower())

    def test_get_cache_key_uses_email_as_fallback(self):
        """Test that email is used when username is not provided"""
        throttle = UsernameRateThrottle()
        request = MagicMock()
        request.method = "POST"
        request.data = {"email": "test@example.com"}

        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
        self.assertIn("test@example.com", cache_key.lower())

    def test_parse_rate_handles_15min_format(self):
        """Test parsing of '5/15min' rate format"""
        throttle = UsernameRateThrottle()
        num_requests, duration = throttle.parse_rate("5/15min")
        self.assertEqual(num_requests, 5)
        self.assertEqual(duration, 15 * 60)  # 900 seconds

    def test_parse_rate_handles_standard_formats(self):
        """Test parsing of standard rate formats"""
        throttle = UsernameRateThrottle()

        # Standard minute format
        num_requests, duration = throttle.parse_rate("10/minute")
        self.assertEqual(num_requests, 10)
        self.assertEqual(duration, 60)

    def test_parse_rate_handles_invalid_15min_format(self):
        """Test parsing of invalid '15min' rate format"""
        throttle = UsernameRateThrottle()
        num_requests, duration = throttle.parse_rate("invalid/15min")
        self.assertIsNone(num_requests)
        self.assertIsNone(duration)


class AdminLoginThrottleTests(TestCase):
    """Test AdminLoginThrottle class"""

    def test_scope_is_admin_login(self):
        """Test that scope is correctly set"""
        throttle = AdminLoginThrottle()
        self.assertEqual(throttle.scope, "admin_login")

    def test_fallback_rate_is_5_per_15min(self):
        """Test that fallback rate is 5/15min"""
        self.assertEqual(AdminLoginThrottle.fallback_rate, "5/15min")

    def test_get_cache_key_returns_none_for_get_request(self):
        """Test that GET requests don't get throttled"""
        throttle = AdminLoginThrottle()
        request = MagicMock()
        request.method = "GET"
        request.path = "/admin/login/"

        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNone(cache_key)

    def test_get_cache_key_returns_none_for_non_admin_path(self):
        """Test that non-admin paths don't get throttled"""
        throttle = AdminLoginThrottle()
        request = MagicMock()
        request.method = "POST"
        request.path = "/api/login/"

        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNone(cache_key)

    def test_get_cache_key_works_for_admin_login(self):
        """Test that admin login POST gets a cache key"""
        throttle = AdminLoginThrottle()
        request = MagicMock()
        request.method = "POST"
        request.path = "/admin/login/"
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        # Mock get_ident to return a known value
        with patch.object(throttle, "get_ident", return_value="127.0.0.1"):
            cache_key = throttle.get_cache_key(request, None)
            self.assertIsNotNone(cache_key)
            self.assertIn("admin_login", cache_key)

    def test_parse_rate_handles_15min_format(self):
        """Test parsing of '5/15min' rate format"""
        throttle = AdminLoginThrottle()
        num_requests, duration = throttle.parse_rate("5/15min")
        self.assertEqual(num_requests, 5)
        self.assertEqual(duration, 15 * 60)

    def test_parse_rate_handles_3_per_15min(self):
        """Test parsing of different request counts"""
        throttle = AdminLoginThrottle()
        num_requests, duration = throttle.parse_rate("3/15min")
        self.assertEqual(num_requests, 3)
        self.assertEqual(duration, 15 * 60)


class ThrottleIntegrationTests(TestCase):
    """Integration tests for throttle behavior"""

    def test_login_throttle_has_correct_scope_settings(self):
        """Test that login throttle scope is in settings"""
        rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("login", rates)

    def test_username_throttle_has_correct_scope_settings(self):
        """Test that login_username throttle scope is in settings"""
        rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("login_username", rates)

    def test_admin_throttle_has_correct_scope_settings(self):
        """Test that admin_login throttle scope is in settings"""
        rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("admin_login", rates)

    def test_refresh_throttle_has_correct_scope_settings(self):
        """Test that refresh throttle scope is in settings"""
        rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("refresh", rates)
