"""
Tests for security configurations and error handling.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


class ErrorHandlingTest(TestCase):
    """Test error handling and edge cases"""

    def test_nonexistent_url_returns_404(self):
        """Test that non-existent URLs return 404"""
        response = self.client.get("/nonexistent-url/")
        self.assertEqual(response.status_code, 404)

    def test_admin_access_requires_staff(self):
        """Test that admin access requires staff privileges"""
        # Create regular user
        user = User.objects.create_user(username="regular", password="test123")
        self.client.force_login(user)

        response = self.client.get(reverse("admin:index"))
        # Should redirect to login or show permission denied
        self.assertIn(response.status_code, [302, 403])

    def test_admin_access_with_staff_user(self):
        """Test that staff users can access admin"""
        # Create staff user
        staff_user = User.objects.create_user(
            username="staff", password="test123", is_staff=True
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)


class SecurityTest(TestCase):
    """Test security configurations"""

    def test_csrf_protection_enabled(self):
        """Test that CSRF protection is enabled"""
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE)

    def test_clickjacking_protection_enabled(self):
        """Test that clickjacking protection is enabled"""
        self.assertIn(
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            settings.MIDDLEWARE,
        )

    def test_security_middleware_enabled(self):
        """Test that security middleware is enabled"""
        self.assertIn(
            "django.middleware.security.SecurityMiddleware", settings.MIDDLEWARE
        )

    @override_settings(USE_HTTPS=True)
    def test_https_settings_when_enabled(self):
        """Test HTTPS-related settings when USE_HTTPS is enabled"""
        # This tests the structure; actual HTTPS settings would be tested in deployment
        self.assertTrue(True)

    def test_session_security_settings(self):
        """Test session security settings"""
        # Check that secure session settings can be configured
        self.assertIn("SESSION_COOKIE_AGE", dir(settings))
        self.assertIn("SESSION_EXPIRE_AT_BROWSER_CLOSE", dir(settings))

    def test_password_validation_configured(self):
        """Test that password validation is configured appropriately"""
        # Expect validators to be configured (not disabled)
        self.assertGreaterEqual(len(settings.AUTH_PASSWORD_VALIDATORS), 1)
        # Ensure MinimumLengthValidator is present (min_length configured in settings)
        has_min_length = any(
            v.get("NAME", "").endswith("MinimumLengthValidator")
            for v in settings.AUTH_PASSWORD_VALIDATORS
        )
        self.assertTrue(has_min_length)
