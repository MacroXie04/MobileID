"""
Tests for API throttling configuration.
"""

from django.conf import settings
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
            "registration",
            "barcode_generation",
            "barcode_management",
            "user_profile",
        ]

        for rate in expected_rates:
            self.assertIn(rate, throttle_rates)

    def test_throttling_classes_configured(self):
        """Test that throttling classes are configured"""
        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])

        expected_classes = [
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
        ]

        for throttle_class in expected_classes:
            self.assertIn(throttle_class, throttle_classes)
