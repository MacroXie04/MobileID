"""
Tests for security-related settings: passwords, CSRF,
cookies, admin, and account lockout.
"""

from django.conf import settings
from django.test import TestCase


class SecuritySettingsTest(TestCase):
    """Test security-related settings"""

    def test_password_validators_configured(self):
        """Test that password validators are configured"""
        validators = settings.AUTH_PASSWORD_VALIDATORS
        self.assertGreater(len(validators), 0)

        # Check for minimum length validator
        validator_names = [v["NAME"] for v in validators]
        self.assertTrue(
            any("MinimumLengthValidator" in name for name in validator_names)
        )

    def test_password_minimum_length(self):
        """Test that minimum password length is configured"""
        for validator in settings.AUTH_PASSWORD_VALIDATORS:
            if "MinimumLengthValidator" in validator["NAME"]:
                min_length = validator.get("OPTIONS", {}).get("min_length", 8)
                self.assertGreaterEqual(min_length, 10)

    def test_password_hashers_configured(self):
        """Test that secure password hashers are configured"""
        hashers = settings.PASSWORD_HASHERS
        self.assertGreater(len(hashers), 0)
        # Argon2 should be the primary hasher
        self.assertIn("Argon2PasswordHasher", hashers[0])

    def test_csrf_settings_configured(self):
        """Test that CSRF settings are configured"""
        self.assertIsNotNone(settings.CSRF_COOKIE_SAMESITE)
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, "Lax")

    def test_session_cookie_settings_configured(self):
        """Test that session cookie settings are configured"""
        self.assertIsNotNone(settings.SESSION_COOKIE_SAMESITE)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")

    def test_xframe_options_configured(self):
        """Test that X-Frame-Options is configured"""
        self.assertEqual(settings.X_FRAME_OPTIONS, "SAMEORIGIN")

    def test_content_type_nosniff_enabled(self):
        """Test that content type nosniff is enabled"""
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)


class AdminSecuritySettingsTest(TestCase):
    """Test admin-related security settings"""

    def test_admin_url_path_configured(self):
        """Test that admin URL path is configured"""
        self.assertIsNotNone(settings.ADMIN_URL_PATH)

    def test_admin_session_cookie_age_configured(self):
        """Test that admin session cookie age is configured"""
        self.assertIsNotNone(settings.ADMIN_SESSION_COOKIE_AGE)
        # Admin sessions should be shorter than regular sessions
        self.assertLess(
            settings.ADMIN_SESSION_COOKIE_AGE,
            settings.SESSION_COOKIE_AGE,
        )

    def test_admin_allowed_ips_is_list(self):
        """Test that admin allowed IPs is a list"""
        self.assertIsInstance(settings.ADMIN_ALLOWED_IPS, list)


class AccountSecuritySettingsTest(TestCase):
    """Test account security settings"""

    def test_max_failed_login_attempts_configured(self):
        """Test that max failed login attempts is configured"""
        self.assertIsNotNone(settings.MAX_FAILED_LOGIN_ATTEMPTS)
        self.assertGreater(settings.MAX_FAILED_LOGIN_ATTEMPTS, 0)

    def test_account_lockout_duration_configured(self):
        """Test that account lockout duration is configured"""
        self.assertIsNotNone(settings.ACCOUNT_LOCKOUT_DURATION)
        self.assertGreater(settings.ACCOUNT_LOCKOUT_DURATION, 0)
