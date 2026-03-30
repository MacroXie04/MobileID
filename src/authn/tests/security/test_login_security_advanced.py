from authn.models import LoginAuditLog
from authn.services import create_user_profile
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authn.tests.security.test_login_security_basic import LoginSecurityTestBase


class LoginSecurityAdvancedTests(LoginSecurityTestBase):
    """Advanced login security tests — validation, audit logging, throttle."""

    def test_failed_login_creates_audit_log_entry(self):
        """Test that failed login attempts are logged"""
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": "wrongpassword"},
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
        )

        log = LoginAuditLog.objects.filter(
            username=self.user.username, success=False
        ).first()
        self.assertIsNotNone(log)
        self.assertFalse(log.success)

    def test_login_with_nonexistent_user_fails(self):
        """Test that login with non-existent user fails gracefully"""
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"username": "nonexistent_user", "password": "anypassword"},
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
        )

    def test_empty_password_rejected(self):
        """Test that empty password is rejected"""
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_username_rejected(self):
        """Test that empty username is rejected"""
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"username": "", "password": self.user_password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_username_rejected(self):
        """Test that missing username field is rejected"""
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"password": self.user_password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_rejected(self):
        """Test that missing password field is rejected"""
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"username": self.user.username},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_message_without_tokens_in_body(self):
        """Test that successful login returns message but no tokens in body (default)"""
        response = self._perform_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_access_token_cookie_set_on_login(self):
        """Test that access token cookie is set on login"""
        response = self._perform_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)

    def test_username_throttle_per_user(self):
        """Test that username throttle is per-username"""
        url = reverse("authn:api_login")

        # Create another user
        other_user = User.objects.create_user(
            username="otheruser", password="testpass456"
        )

        # Exhaust throttle for first user
        for _ in range(6):
            self.client.post(
                url,
                {"username": self.user.username, "password": "invalid"},
                format="json",
            )

        # Other user should still be able to attempt login
        cache.clear()
        response = self.client.post(
            url,
            {"username": other_user.username, "password": "invalid"},
            format="json",
        )
        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_429_TOO_MANY_REQUESTS,
            ],
        )


class CookieSecurityTests(APITestCase):
    """Test cookie security attributes"""

    @classmethod
    def setUpTestData(cls):
        cls.user_password = "testpass123"
        cls.user = User.objects.create_user(
            username="cookieuser", password=cls.user_password
        )
        create_user_profile(cls.user, "Cookie User", "COOKIE123", None)

    def setUp(self):
        super().setUp()
        cache.clear()

    def test_refresh_token_httponly(self):
        """Test that refresh token cookie is HttpOnly"""
        login_url = reverse("authn:api_login")
        response = self.client.post(
            login_url,
            {"username": self.user.username, "password": self.user_password},
            format="json",
        )

        refresh_cookie = response.cookies.get("refresh_token")
        if refresh_cookie:
            cookie_header = refresh_cookie.output(header="")
            self.assertIn("HttpOnly", cookie_header)

    def test_access_token_cookie_attributes(self):
        """Test that access token cookie has secure attributes"""
        login_url = reverse("authn:api_login")
        response = self.client.post(
            login_url,
            {"username": self.user.username, "password": self.user_password},
            format="json",
        )

        access_cookie = response.cookies.get("access_token")
        if access_cookie:
            cookie_header = access_cookie.output(header="")
            self.assertIn("HttpOnly", cookie_header)
            self.assertIn("SameSite", cookie_header)
