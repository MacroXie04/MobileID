from datetime import timedelta

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from authn.repositories import SecurityRepository
from authn.session_revocation import CURRENT_SESSION_IAT_LEEWAY_SECONDS


@override_settings(THROTTLES_ENABLED=False)
class CookieJWTAuthenticationTests(APITestCase):
    """Tests for CookieJWTAuthentication in authn/authentication.py."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="cookieuser", password="pass123")
        # Use user_info endpoint as a simple authenticated GET endpoint
        cls.auth_url = reverse("authn:api_user_info")

    def setUp(self):
        self.client = APIClient()

    def test_authenticate_from_authorization_header(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "cookieuser")

    def test_authenticate_from_cookie(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "cookieuser")

    def test_authenticate_returns_none_when_no_token(self):
        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_jti_rejects_request(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        # Blacklist the access token's JTI
        jti = access_token["jti"]
        SecurityRepository.blacklist_token(
            jti=jti,
            user_id=self.user.id,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.auth_url)
        # Should be rejected (401 or 403)
        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_session_revocation_window_rejects_token(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        # Create a session revocation entry matching the token's iat
        iat = int(access_token["iat"])
        session_key = f"session_{self.user.id}_{iat}"
        SecurityRepository.blacklist_token(
            jti=session_key,
            user_id=self.user.id,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.auth_url)
        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_session_revocation_window_allows_nearby_nonmatching_session(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        nearby_other_session_iat = (
            int(access_token["iat"]) + CURRENT_SESSION_IAT_LEEWAY_SECONDS + 1
        )
        session_key = f"session_{self.user.id}_{nearby_other_session_iat}"
        SecurityRepository.blacklist_token(
            jti=session_key,
            user_id=self.user.id,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "cookieuser")

    def test_cookie_auth_post_requires_csrf(self):
        """POST with cookie auth but no CSRF token should fail."""
        csrf_client = APIClient(enforce_csrf_checks=True)
        refresh = RefreshToken.for_user(self.user)
        csrf_client.cookies["access_token"] = str(refresh.access_token)

        # Use profile endpoint (requires auth) to test CSRF enforcement on PUT
        profile_url = reverse("authn:api_profile")
        response = csrf_client.put(profile_url, {"name": "Test"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cookie_auth_get_skips_csrf(self):
        """GET with cookie auth should work without CSRF."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(refresh.access_token)

        response = self.client.get(self.auth_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
