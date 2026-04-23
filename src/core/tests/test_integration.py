"""
Integration tests for the complete application.
"""

from authn.services import create_user_profile
from django.contrib.auth.models import User
from django.urls import reverse
from index.repositories import SettingsRepository
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class IntegrationTest(DynamoDBTestMixin, APITestCase):
    """Integration tests for the complete application"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="integrationtest", password="testpass123"
        )
        create_user_profile(self.user, "Integration User", "INT123", None)

    def test_complete_authentication_flow(self):
        """
        Test complete authentication flow from login to authenticated request
        """
        # Test login
        login_url = reverse("authn:api_token_obtain_pair")
        login_data = {"username": "integrationtest", "password": "testpass123"}

        response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check cookies are set
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

        # Test authenticated request using JWT
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        user_info_url = reverse("authn:api_user_info")
        response = self.client.get(user_info_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "integrationtest")

    def test_barcode_generation_no_selection(self):
        """Test barcode generation returns error when no barcode is selected"""
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Clear the auto-assigned identification barcode from settings
        SettingsRepository.set_active_barcode(self.user.id, None)

        # No barcode selected — should return error
        generate_url = reverse("index:api_generate_barcode")
        response = self.client.post(generate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "error")

    def test_unauthenticated_access_denied(self):
        """Test that protected endpoints require authentication"""
        protected_urls = [
            reverse("authn:api_user_info"),
            reverse("index:api_generate_barcode"),
            reverse("index:api_barcode_dashboard"),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cors_preflight_request(self):
        """Test CORS preflight request handling"""
        response = self.client.options(
            reverse("authn:api_token_obtain_pair"),
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="Content-Type",
        )

        # Should not return 405 Method Not Allowed
        self.assertNotEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
