from unittest.mock import patch

from authn.services import create_user_profile
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


class CookieAuthenticationTest(APITestCase):
    """Test cookie-based authentication flow"""

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username="cookieuser", password="testpass123"
        )
        create_user_profile(self.user, "Cookie User", "COOK123", None)

    def test_login_sets_auth_cookies(self):
        """POST to login sets access_token and refresh_token cookies"""
        url = reverse("authn:api_token_obtain_pair")
        response = self.client.post(
            url, {"username": "cookieuser", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        # Cookies should be httponly
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_cookie_auth_works_for_api_calls(self):
        """Setting access_token cookie authenticates GET requests"""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)

        url = reverse("authn:api_user_info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "cookieuser")

    def test_cookie_auth_enforces_csrf_on_write(self):
        """Cookie-authenticated PUT without CSRF token returns 403"""
        csrf_client = APIClient(enforce_csrf_checks=True)
        refresh = RefreshToken.for_user(self.user)
        csrf_client.cookies["access_token"] = str(refresh.access_token)

        url = reverse("authn:api_profile")
        response = csrf_client.put(url, {"name": "New"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refresh_via_cookie(self):
        """Setting refresh_token cookie and POSTing to refresh returns new cookies"""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["refresh_token"] = str(refresh)

        url = reverse("authn:api_token_refresh")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_logout_clears_cookies(self):
        """POST to logout deletes auth cookies"""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

        # Get a CSRF token first
        csrf_response = self.client.get(reverse("authn:api_csrf_token"))
        csrf_token = csrf_response.cookies["csrftoken"].value

        url = reverse("authn:api_logout")
        response = self.client.post(url, HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Cookies should be deleted (max-age=0)
        self.assertEqual(response.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)


class TokenErrorExceptionTest(APITestCase):
    """Test TokenError exception paths in login serializers"""

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username="tokenerr", password="testpass123"
        )
        create_user_profile(self.user, "Token Err", "TERR123", None)

    @patch(
        "rest_framework_simplejwt.serializers.TokenObtainPairSerializer.validate",
        side_effect=TokenError("Token is invalid"),
    )
    def test_plaintext_serializer_catches_token_error(self, mock_validate):
        """PlaintextLoginSerializer converts TokenError to 401"""
        url = reverse("authn:api_token_obtain_pair")
        response = self.client.post(
            url, {"username": "tokenerr", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
