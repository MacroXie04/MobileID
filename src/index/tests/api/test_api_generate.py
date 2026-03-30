from authn.services import create_user_profile
from django.contrib.auth.models import User
from django.urls import reverse
from index.models import (
    Barcode,
    BarcodeUserProfile,
    UserBarcodeSettings,
)
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class GenerateBarcodeAPITest(APITestCase):
    """Test GenerateBarcodeAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        create_user_profile(self.user, "Test User", "TEST123", None)

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_generate_barcode_success(self):
        """Test successful barcode generation with selected barcode"""
        # Select the identification barcode created by create_user_profile
        ident = Barcode.objects.get(user=self.user, barcode_type="Identification")
        UserBarcodeSettings.objects.filter(user=self.user).update(barcode=ident)

        url = reverse("index:api_generate_barcode")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["barcode_type"], "Identification")

    def test_generate_barcode_unauthenticated(self):
        """Test barcode generation without authentication"""
        self.client.credentials()  # Remove authentication

        url = reverse("index:api_generate_barcode")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ActiveProfileAPITest(APITestCase):
    """Tests for ActiveProfileAPIView"""

    def setUp(self):
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
        # Create barcode and link settings and profile
        bc = Barcode.objects.create(
            user=self.user,
            barcode="activeprof123456",
            barcode_type="Others",
        )
        UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=bc,
            associate_user_profile_with_barcode=True,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=bc,
            name="Test User",
            information_id="TEST123",
            user_profile_img=None,
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
        bc = Barcode.objects.create(
            user=self.user,
            barcode="activeprofavatar",
            barcode_type="Others",
        )
        UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=bc,
            associate_user_profile_with_barcode=True,
        )
        # Store raw base64 without data URI; endpoint should prefix data:image/png  # noqa: E501
        BarcodeUserProfile.objects.create(
            linked_barcode=bc,
            name="Avatar User",
            information_id="AVT123",
            user_profile_img="dGVzdA==",
        )
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_info"]["has_avatar"])
        self.assertTrue(
            resp.data["profile_info"]["avatar_data"].startswith("data:image")
        )
