from authn.models import UserProfile
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin


class BarcodeDashboardTestBase(DynamoDBTestMixin, APITestCase):
    """Shared setUp and helpers for BarcodeDashboardAPITest split files."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        UserProfile.objects.create(
            user=self.user,
            name="Test User",
            information_id="TEST123",
        )

    def _authenticate_user(self, user):
        """Helper to authenticate a user"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
