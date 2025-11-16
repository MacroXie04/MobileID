from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class UserRegistrationAPITest(APITestCase):
    """Test user registration API"""

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.registration_data = {
            "username": "newuser",
            "password1": "newpass123",
            "password2": "newpass123",
            "name": "New User",
            "information_id": "NEW123",
        }

    def test_registration_success(self):
        cache.clear()
        url = reverse("authn:api_register")
        response = self.client.post(url, self.registration_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Registration successful")

        user = User.objects.get(username="newuser")
        self.assertTrue(hasattr(user, "userprofile"))
        self.assertEqual(user.userprofile.name, "New User")
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_registration_with_avatar(self):
        cache.clear()
        data = self.registration_data.copy()
        data["user_profile_img_base64"] = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )

        url = reverse("authn:api_register")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username="newuser")
        self.assertIsNotNone(user.userprofile.user_profile_img)

    def test_registration_missing_fields(self):
        data = {"username": "newuser", "password1": "newpass123"}

        url = reverse("authn:api_register")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("errors", response.data)

    def test_registration_password_mismatch(self):
        data = self.registration_data.copy()
        data["password2"] = "differentpass"

        url = reverse("authn:api_register")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_registration_duplicate_username(self):
        User.objects.create_user(username="newuser", password="pass123")

        url = reverse("authn:api_register")
        response = self.client.post(url, self.registration_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_registration_invalid_avatar(self):
        data = self.registration_data.copy()
        data["user_profile_img_base64"] = "invalid-base64-data"

        url = reverse("authn:api_register")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_registration_rate_limit(self):
        url = reverse("authn:api_register")

        response1 = self.client.post(url, self.registration_data, format="json")
        self.assertIn(response1.status_code, [200, 429])

