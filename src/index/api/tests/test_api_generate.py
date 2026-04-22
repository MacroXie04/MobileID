from authn.services import create_user_profile
from django.contrib.auth.models import User
from django.urls import reverse
from index.repositories import BarcodeRepository, SettingsRepository
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin


class GenerateBarcodeAPITest(DynamoDBTestMixin, APITestCase):
    """Test GenerateBarcodeAPIView"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        create_user_profile(self.user, "Test User", "TEST123", None)

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_generate_barcode_no_selection(self):
        """Test barcode generation returns error when no barcode is selected.

        Note: create_user_profile now auto-creates an Identification barcode
        and sets it as active. To test "no selection", we clear the setting.
        """
        # Clear the auto-assigned barcode
        SettingsRepository.set_active_barcode(self.user.id, None)

        url = reverse("index:api_generate_barcode")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "error")

    def test_generate_barcode_unauthenticated(self):
        """Test barcode generation without authentication"""
        self.client.credentials()  # Remove authentication

        url = reverse("index:api_generate_barcode")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ActiveProfileAPITest(DynamoDBTestMixin, APITestCase):
    """Tests for ActiveProfileAPIView"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_user_without_settings_gets_none(self):
        self._auth(self.user)
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["profile_info"])

    def test_user_with_linked_profile(self):
        self._auth(self.user)
        # Create barcode with profile data and link in settings
        bc = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="activeprof123456",
            barcode_type="Others",
            owner_username=self.user.username,
            profile_name="Test User",
            profile_info_id="TEST123",
        )
        SettingsRepository.update(
            self.user.id,
            active_barcode_uuid=bc["barcode_uuid"],
            associate_user_profile_with_barcode=True,
        )
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(resp.data["profile_info"])
        self.assertEqual(resp.data["profile_info"]["name"], "Test User")
        self.assertEqual(resp.data["profile_info"]["information_id"], "TEST123")
        self.assertFalse(resp.data["profile_info"]["has_avatar"])

    def test_user_with_avatar_adds_data_uri(self):
        self._auth(self.user)
        bc = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="activeprofavatar",
            barcode_type="Others",
            owner_username=self.user.username,
            profile_name="Avatar User",
            profile_info_id="AVT123",
            profile_avatar="dGVzdA==",
        )
        SettingsRepository.update(
            self.user.id,
            active_barcode_uuid=bc["barcode_uuid"],
            associate_user_profile_with_barcode=True,
        )
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_info"]["has_avatar"])
        self.assertTrue(
            resp.data["profile_info"]["avatar_data"].startswith("data:image")
        )
