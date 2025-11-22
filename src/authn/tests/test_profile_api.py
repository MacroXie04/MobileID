from authn.services.webauthn import create_user_profile
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class UserProfileAPITest(APITestCase):
    """Test user profile management API"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        create_user_profile(self.user, "Test User", "TEST123", None)

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_get_profile_success(self):
        url = reverse("authn:api_profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["name"], "Test User")
        self.assertEqual(response.data["data"]["information_id"], "TEST123")

    def test_update_profile_success(self):
        url = reverse("authn:api_profile")
        data = {"name": "Updated Name", "information_id": "UPDATED123"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.name, "Updated Name")
        self.assertEqual(self.user.userprofile.information_id, "UPDATED123")

    def test_update_profile_with_avatar(self):
        url = reverse("authn:api_profile")
        avatar_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+"
            "hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        data = {"name": "Updated Name", "user_profile_img_base64": avatar_b64}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.user_profile_img, avatar_b64)

    def test_update_profile_empty_fields(self):
        url = reverse("authn:api_profile")
        data = {"name": "", "information_id": "   "}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("errors", response.data)

    def test_update_profile_invalid_avatar(self):
        url = reverse("authn:api_profile")
        data = {"user_profile_img_base64": "invalid-base64-data"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_profile_unauthenticated(self):
        self.client.credentials()

        url = reverse("authn:api_profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
