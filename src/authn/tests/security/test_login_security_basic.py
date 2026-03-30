from authn.authentication import CookieJWTAuthentication
from authn.models import LoginAuditLog
from authn.services import create_user_profile
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.urls import reverse
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class LoginSecurityTestBase(APITestCase):
    """Base class with shared setUp for LoginSecurityTests split."""

    @classmethod
    def setUpTestData(cls):
        cls.user_password = "testpass123"
        cls.user = User.objects.create_user(
            username="secureuser", password=cls.user_password
        )
        create_user_profile(cls.user, "Secure User", "SECURE123", None)

    def setUp(self):
        super().setUp()
        cache.clear()
        LoginAuditLog.objects.all().delete()

    def _perform_login(self):
        url = reverse("authn:api_login")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": self.user_password},
            format="json",
        )
        return response


class LoginSecurityBasicTests(LoginSecurityTestBase):
    """Basic login, cookie, and CSRF behavior tests."""

    def test_csrf_endpoint_sets_csrf_and_csp(self):
        url = reverse("authn:api_csrf_token")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrfToken", response.data)
        self.assertIn("Content-Security-Policy", response)
        self.assertIn("csrftoken", response.cookies)

    def test_refresh_cookie_attributes(self):
        response = self._perform_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_cookie = response.cookies.get("refresh_token")
        self.assertIsNotNone(refresh_cookie)
        cookie_header = refresh_cookie.output(header="")
        self.assertEqual(refresh_cookie["path"], "/authn/")
        self.assertEqual(refresh_cookie["samesite"], "Lax")
        if settings.SESSION_COOKIE_SECURE:
            self.assertIn("Secure", cookie_header)
        else:
            self.assertNotIn("Secure", cookie_header)
        self.assertIn("HttpOnly", cookie_header)

    def test_token_refresh_rotates_cookie(self):
        login_response = self._perform_login()
        old_refresh = login_response.cookies["refresh_token"].value
        refresh_url = reverse("authn:api_token_refresh")
        refresh_response = self.client.post(
            refresh_url,
            {"refresh": old_refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        new_refresh_cookie = refresh_response.cookies.get("refresh_token")
        self.assertIsNotNone(new_refresh_cookie)
        new_cookie_header = new_refresh_cookie.output(header="")
        self.assertNotEqual(new_refresh_cookie.value, old_refresh)
        if settings.SESSION_COOKIE_SECURE:
            self.assertIn("Secure", new_cookie_header)
        else:
            self.assertNotIn("Secure", new_cookie_header)
        self.assertIn("HttpOnly", new_cookie_header)
        self.assertEqual(new_refresh_cookie["path"], "/authn/")

    def test_login_creates_audit_log_entry(self):
        response = self._perform_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = LoginAuditLog.objects.filter(username=self.user.username).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.success)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.ip_address, "127.0.0.1")

    def test_login_rate_throttle_triggers(self):
        url = reverse("authn:api_login")
        payload = {"username": self.user.username, "password": "wrong"}
        last_status = None
        for _ in range(6):
            response = self.client.post(url, payload, format="json")
            last_status = response.status_code
        self.assertEqual(last_status, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_csrf_enforced_for_cookie_authenticated_put(self):
        factory = APIRequestFactory()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        django_request = factory.put(
            "/authn/profile/",
            {"name": "Updated Name", "information_id": "SECURE123"},
            format="json",
        )
        django_request._dont_enforce_csrf_checks = False
        csrf_token_value = get_token(django_request)
        django_request.COOKIES["access_token"] = access_token
        django_request.COOKIES["csrftoken"] = csrf_token_value
        request = Request(django_request)

        authenticator = CookieJWTAuthentication()
        with self.assertRaises(exceptions.PermissionDenied):
            authenticator.authenticate(request)

        django_request.META["HTTP_X_CSRFTOKEN"] = csrf_token_value
        authed_user, _ = authenticator.authenticate(Request(django_request))
        self.assertEqual(authed_user, self.user)
