from io import BytesIO
from unittest.mock import patch

from PIL import Image
from authn.services.webauthn import create_user_profile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class AvatarUploadAPITest(APITestCase):
    """Test avatar upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        create_user_profile(self.user, "Test User", "TEST123", None)

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def _create_test_image(self):
        image = Image.new("RGB", (100, 100), color="red")
        image_io = BytesIO()
        image.save(image_io, format="PNG")
        image_io.seek(0)
        return image_io

    def test_avatar_upload_success(self):
        url = reverse("authn:api_avatar_upload")

        image_content = self._create_test_image().getvalue()
        image_file = SimpleUploadedFile(
            "test.png", image_content, content_type="image/png"
        )

        response = self.client.post(
            url, {"avatar": image_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.user.userprofile.refresh_from_db()
        self.assertIsNotNone(self.user.userprofile.user_profile_img)

    def test_avatar_upload_no_file(self):
        url = reverse("authn:api_avatar_upload")
        response = self.client.post(url, {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_avatar_upload_invalid_file_type(self):
        url = reverse("authn:api_avatar_upload")
        text_file = SimpleUploadedFile(
            "test.txt", b"not an image", content_type="text/plain"
        )

        response = self.client.post(
            url, {"avatar": text_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_avatar_upload_oversized_file(self):
        url = reverse("authn:api_avatar_upload")

        with patch(
            "django.core.files.uploadedfile.InMemoryUploadedFile.size",
            6 * 1024 * 1024,
        ):
            image_file = self._create_test_image()

            response = self.client.post(
                url, {"avatar": image_file}, format="multipart"
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data["success"])
