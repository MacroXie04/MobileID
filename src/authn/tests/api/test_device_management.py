from datetime import timedelta

from django.contrib.auth.models import User
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
from authn.models import LoginAuditLog
from authn.repositories import SecurityRepository


class _DeviceTestMixin:
    """Shared helpers for device management tests."""

    def _create_session(
        self, user, user_agent="", ip_address="127.0.0.1", time_offset=None
    ):
        """
        Create a refresh token + OutstandingToken + LoginAuditLog entry
        simulating a login session.

        time_offset: timedelta to shift the OutstandingToken.created_at
            (used to make sessions distinguishable by iat).
        """
        refresh = RefreshToken.for_user(user)
        _ensure_outstanding_token(str(refresh))

        # Find the OutstandingToken just created
        token = OutstandingToken.objects.filter(user=user, jti=refresh["jti"]).first()

        # Shift created_at if requested (to simulate sessions from different times)
        if time_offset and token:
            OutstandingToken.objects.filter(pk=token.pk).update(
                created_at=token.created_at + time_offset
            )
            token.refresh_from_db()

        # Create a matching login audit log entry
        if token:
            LoginAuditLog.objects.create(
                user=user,
                username=user.username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                created_at=token.created_at,
            )

        return refresh, token

    def _auth_with_session(self, client, refresh):
        """Authenticate the API client with the given refresh token's access token."""
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")


@override_settings(THROTTLES_ENABLED=False)
class DeviceListingTests(_DeviceTestMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="devuser", password="pass123")
        cls.url = reverse("authn:api_devices_list")

    def setUp(self):
        self.client = APIClient()

    def test_list_devices_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_devices_returns_current_session(self):
        refresh, _ = self._create_session(self.user)
        self._auth_with_session(self.client, refresh)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

        current_devices = [d for d in response.data["devices"] if d["is_current"]]
        self.assertEqual(len(current_devices), 1)

    def test_list_devices_multiple_sessions(self):
        # Current session (no offset - iat matches the JWT)
        refresh1, _ = self._create_session(
            self.user,
            user_agent="Chrome/100 (Macintosh; Mac OS X)",
        )
        # Other sessions with shifted timestamps so they don't match current iat
        self._create_session(
            self.user,
            user_agent="Safari/17 (iPhone; CPU iPhone OS 17_0)",
            time_offset=timedelta(minutes=-10),
        )
        self._create_session(
            self.user,
            user_agent="Firefox/120 (X11; Linux x86_64)",
            time_offset=timedelta(minutes=-20),
        )

        self._auth_with_session(self.client, refresh1)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        # Verify all expected fields are present
        device = response.data["devices"][0]
        expected_fields = {
            "id",
            "jti",
            "device_name",
            "browser",
            "os",
            "device_type",
            "ip_address",
            "user_agent",
            "created_at",
            "expires_at",
            "last_active",
            "is_current",
        }
        self.assertTrue(expected_fields.issubset(set(device.keys())))

    def test_list_devices_excludes_blacklisted_tokens(self):
        refresh1, _ = self._create_session(self.user)
        refresh2, token2 = self._create_session(
            self.user, time_offset=timedelta(minutes=-10)
        )

        # Blacklist the second session's refresh token
        BlacklistedToken.objects.create(token=token2)

        self._auth_with_session(self.client, refresh1)
        response = self.client.get(self.url)

        jtis = [d["jti"] for d in response.data["devices"]]
        self.assertNotIn(str(refresh2["jti"]), jtis)

    def test_list_devices_marks_current_session_correctly(self):
        refresh1, _ = self._create_session(self.user)
        self._create_session(self.user, time_offset=timedelta(minutes=-10))
        self._create_session(self.user, time_offset=timedelta(minutes=-20))

        self._auth_with_session(self.client, refresh1)
        response = self.client.get(self.url)

        current_devices = [d for d in response.data["devices"] if d["is_current"]]
        non_current = [d for d in response.data["devices"] if not d["is_current"]]
        self.assertEqual(len(current_devices), 1)
        self.assertEqual(len(non_current), 2)

    def test_list_devices_parses_user_agent(self):
        refresh, _ = self._create_session(
            self.user,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self._auth_with_session(self.client, refresh)

        response = self.client.get(self.url)
        device = response.data["devices"][0]
        self.assertEqual(device["browser"], "Chrome")
        self.assertEqual(device["os"], "macOS")
        self.assertEqual(device["device_type"], "desktop")


@override_settings(THROTTLES_ENABLED=False)
class DeviceRevocationTests(_DeviceTestMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="revuser", password="pass123")
        cls.other_user = User.objects.create_user(
            username="otheruser", password="pass123"
        )

    def setUp(self):
        self.client = APIClient()

    def test_revoke_device_unauthenticated_returns_401(self):
        url = reverse("authn:api_device_revoke", args=[999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revoke_device_success(self):
        refresh1, _ = self._create_session(self.user)
        _, token2 = self._create_session(self.user, time_offset=timedelta(minutes=-10))

        self._auth_with_session(self.client, refresh1)
        url = reverse("authn:api_device_revoke", args=[token2.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BlacklistedToken.objects.filter(token=token2).exists())
        # Verify session access token blacklist entry was created in DynamoDB
        session_ts = int(token2.created_at.timestamp())
        session_key = f"session_{self.user.id}_{session_ts}"
        self.assertTrue(SecurityRepository.is_blacklisted(session_key))

    def test_revoke_device_prevents_revoking_current_session(self):
        refresh, token = self._create_session(self.user)
        self._auth_with_session(self.client, refresh)

        url = reverse("authn:api_device_revoke", args=[token.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot revoke current", response.data["error"])

    def test_revoke_device_not_found_returns_404(self):
        refresh, _ = self._create_session(self.user)
        self._auth_with_session(self.client, refresh)

        url = reverse("authn:api_device_revoke", args=[99999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_device_other_users_token_returns_404(self):
        refresh_mine, _ = self._create_session(self.user)
        _, other_token = self._create_session(
            self.other_user, time_offset=timedelta(minutes=-10)
        )

        self._auth_with_session(self.client, refresh_mine)
        url = reverse("authn:api_device_revoke", args=[other_token.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_device_already_revoked_returns_400(self):
        refresh1, _ = self._create_session(self.user)
        _, token2 = self._create_session(self.user, time_offset=timedelta(minutes=-10))

        BlacklistedToken.objects.create(token=token2)

        self._auth_with_session(self.client, refresh1)
        url = reverse("authn:api_device_revoke", args=[token2.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already revoked", response.data["error"])

    def test_revoke_device_via_post_method(self):
        refresh1, _ = self._create_session(self.user)
        _, token2 = self._create_session(self.user, time_offset=timedelta(minutes=-10))

        self._auth_with_session(self.client, refresh1)
        url = reverse("authn:api_device_revoke", args=[token2.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(THROTTLES_ENABLED=False)
class RevokeAllOtherDevicesTests(_DeviceTestMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="revokeall", password="pass123")
        cls.url = reverse("authn:api_devices_revoke_all")

    def setUp(self):
        self.client = APIClient()

    def test_revoke_all_unauthenticated_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revoke_all_other_devices_success(self):
        refresh1, _ = self._create_session(self.user)
        self._create_session(self.user, time_offset=timedelta(minutes=-10))
        self._create_session(self.user, time_offset=timedelta(minutes=-20))

        self._auth_with_session(self.client, refresh1)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["revoked_count"], 2)
        self.assertTrue(response.data["success"])

    def test_revoke_all_other_devices_no_others(self):
        refresh, _ = self._create_session(self.user)
        self._auth_with_session(self.client, refresh)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["revoked_count"], 0)

    def test_revoke_all_creates_access_token_blacklist_entries(self):
        refresh1, _ = self._create_session(self.user)
        _, token2 = self._create_session(
            self.user, time_offset=timedelta(minutes=-10)
        )
        _, token3 = self._create_session(
            self.user, time_offset=timedelta(minutes=-20)
        )

        self._auth_with_session(self.client, refresh1)

        self.client.delete(self.url)

        # Verify that access token blacklist entries were created in DynamoDB
        # for the two revoked sessions (not the current one)
        session_ts_2 = int(token2.created_at.timestamp())
        session_ts_3 = int(token3.created_at.timestamp())
        session_key_2 = f"session_{self.user.id}_{session_ts_2}"
        session_key_3 = f"session_{self.user.id}_{session_ts_3}"
        self.assertTrue(SecurityRepository.is_blacklisted(session_key_2))
        self.assertTrue(SecurityRepository.is_blacklisted(session_key_3))
