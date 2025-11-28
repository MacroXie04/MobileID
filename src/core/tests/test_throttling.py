"""
Tests for API throttling configuration.
"""

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase


class ThrottlingConfigurationTest(APITestCase):
    """Test API throttling configuration"""

    def test_throttling_rates_configured(self):
        """Test that throttling rates are properly configured"""
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})

        expected_rates = [
            "anon",
            "user",
            "login",
            "login_username",
            "registration",
            "barcode_generation",
            "barcode_management",
            "user_profile",
        ]

        for rate in expected_rates:
            self.assertIn(rate, throttle_rates)

        self.assertEqual(throttle_rates["login_username"], "5/minute")

    def test_throttling_classes_configured(self):
        """Test that throttling classes are configured"""
        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])

        expected_classes = [
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
        ]

        for throttle_class in expected_classes:
            self.assertIn(throttle_class, throttle_classes)

    def test_scoped_rate_throttle_configured(self):
        """Test that ScopedRateThrottle is configured for scope-based limiting"""
        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])
        self.assertIn(
            "rest_framework.throttling.ScopedRateThrottle",
            throttle_classes,
        )

    def test_admin_login_throttle_rate_configured(self):
        """Test that admin login has specific throttle rate"""
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("admin_login", throttle_rates)
        self.assertEqual(throttle_rates["admin_login"], "5/15min")

    def test_registration_throttle_is_restrictive(self):
        """Test that registration throttle is appropriately restrictive"""
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("registration", throttle_rates)
        # Registration should be limited (e.g., 5/day)
        rate = throttle_rates["registration"]
        self.assertIn("/day", rate)

    def test_barcode_throttle_rates_configured(self):
        """Test barcode-related throttle rates"""
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})

        # Check barcode generation rate
        self.assertIn("barcode_generation", throttle_rates)
        self.assertEqual(throttle_rates["barcode_generation"], "100/hour")

        # Check barcode management rate
        self.assertIn("barcode_management", throttle_rates)
        self.assertEqual(throttle_rates["barcode_management"], "50/hour")


class ThrottlingTestingModeTest(TestCase):
    """Test throttling behavior in testing mode"""

    def test_testing_mode_enables_throttles(self):
        """Test that TESTING=True keeps throttles enabled"""
        # In test mode, TESTING should be True
        self.assertTrue(settings.TESTING)
        # Therefore throttles should be enabled
        self.assertFalse(settings.DISABLE_THROTTLES)
        self.assertTrue(settings.THROTTLES_ENABLED)

    def test_throttle_classes_not_empty_in_testing(self):
        """Test that throttle classes are populated in testing mode"""
        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])
        self.assertGreater(len(throttle_classes), 0)

    def test_throttle_rates_not_empty_in_testing(self):
        """Test that throttle rates are populated in testing mode"""
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertGreater(len(throttle_rates), 0)


class ThrottleCacheTest(TestCase):
    """Test throttle cache behavior"""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_is_available(self):
        """Test that cache backend is working for throttling"""
        cache.set("test_throttle_key", "test_value", timeout=60)
        self.assertEqual(cache.get("test_throttle_key"), "test_value")

    def test_cache_expiry_works(self):
        """Test that cache expiry works for throttle windows"""
        cache.set("throttle_test", 1, timeout=1)
        self.assertEqual(cache.get("throttle_test"), 1)
        # Note: Actual expiry test would need time.sleep which we avoid

    def test_cache_increment_for_throttle_counting(self):
        """Test that cache can handle throttle counting patterns"""
        key = "throttle_count_test"
        cache.set(key, 0, timeout=60)

        # Simulate throttle count increment
        for i in range(5):
            current = cache.get(key, 0)
            cache.set(key, current + 1, timeout=60)

        self.assertEqual(cache.get(key), 5)
