"""
Tests for authn.api.webauthn.views.tokens.

Covers the refresh view and `_ensure_outstanding_token`.
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from authn.api.webauthn.views.tokens import _ensure_outstanding_token


User = get_user_model()


class EnsureOutstandingTokenTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="outst", password="pw")

    def test_inserts_row_for_new_jti(self):
        refresh = RefreshToken.for_user(self.user)
        OutstandingToken.objects.filter(jti=refresh["jti"]).delete()

        _ensure_outstanding_token(str(refresh))

        self.assertTrue(OutstandingToken.objects.filter(jti=refresh["jti"]).exists())

    def test_is_idempotent_when_jti_already_tracked(self):
        refresh = RefreshToken.for_user(self.user)
        before = OutstandingToken.objects.filter(jti=refresh["jti"]).count()

        _ensure_outstanding_token(str(refresh))
        _ensure_outstanding_token(str(refresh))

        after = OutstandingToken.objects.filter(jti=refresh["jti"]).count()
        # RefreshToken.for_user may already record the jti; either way it
        # must not duplicate.
        self.assertEqual(after, max(before, 1))

    def test_swallows_errors_on_malformed_token(self):
        # Must not raise — the production code catches and logs.
        try:
            _ensure_outstanding_token("definitely-not-a-token")
        except Exception as exc:  # pragma: no cover - test failure path
            self.fail(f"_ensure_outstanding_token raised: {exc!r}")


class CookieTokenRefreshViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(username="refresher", password="pw")

    def test_returns_400_when_no_refresh_in_body_or_cookie(self):
        url = reverse("authn:api_token_refresh")
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("required", response.data["detail"].lower())

    def test_refresh_via_body_issues_new_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        url = reverse("authn:api_token_refresh")

        response = self.client.post(url, {"refresh": str(refresh)}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tokens are set as httponly cookies; body should be empty by default.
        self.assertIn("access_token", response.cookies)
        self.assertNotIn("access", response.data)

    def test_refresh_via_cookie_issues_new_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["refresh_token"] = str(refresh)
        url = reverse("authn:api_token_refresh")

        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)

    def test_invalid_body_refresh_returns_400(self):
        url = reverse("authn:api_token_refresh")

        response = self.client.post(
            url, {"refresh": "definitely-not-a-token"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid token.")

    def test_blacklisted_refresh_cookie_is_rejected(self):
        refresh = RefreshToken.for_user(self.user)
        # Blacklisting requires the OutstandingToken row to exist first.
        outstanding, _ = OutstandingToken.objects.get_or_create(
            jti=refresh["jti"],
            defaults={
                "user": self.user,
                "token": str(refresh),
                "created_at": refresh.current_time,
                "expires_at": refresh.current_time + refresh.lifetime,
            },
        )
        BlacklistedToken.objects.get_or_create(token=outstanding)

        self.client.cookies["refresh_token"] = str(refresh)
        url = reverse("authn:api_token_refresh")
        response = self.client.post(url, {}, format="json")

        self.assertIn(
            response.status_code,
            {status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED},
        )

    @override_settings(AUTH_EXPOSE_TOKENS_IN_BODY=True)
    def test_expose_tokens_in_body_returns_tokens(self):
        refresh = RefreshToken.for_user(self.user)
        url = reverse("authn:api_token_refresh")

        response = self.client.post(url, {"refresh": str(refresh)}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class LogoutViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(username="bye", password="pw")

    def test_logout_clears_auth_cookies(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["refresh_token"] = str(refresh)
        self.client.cookies["access_token"] = str(refresh.access_token)

        url = reverse("authn:api_logout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Cleared cookies have an empty value with max-age 0.
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_logout_blacklists_refresh_token_when_present(self):
        refresh = RefreshToken.for_user(self.user)
        # Authenticate the request via the access_token cookie; logout is an
        # authenticated endpoint.
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

        url = reverse("authn:api_logout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()
        )

    def test_logout_without_refresh_cookie_still_succeeds(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)

        url = reverse("authn:api_logout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out")


class LoginViewBodyExposureTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(username="loginbody", password="pw12345!")

    def test_login_returns_tokens_in_body_when_flag_enabled(self):
        url = reverse("authn:api_login")
        with override_settings(AUTH_EXPOSE_TOKENS_IN_BODY=True):
            response = self.client.post(
                url, {"username": "loginbody", "password": "pw12345!"}, format="json"
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["message"], "Login successful")

    def test_login_hides_tokens_in_body_by_default(self):
        url = reverse("authn:api_login")
        response = self.client.post(
            url, {"username": "loginbody", "password": "pw12345!"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertIn("access_token", response.cookies)
