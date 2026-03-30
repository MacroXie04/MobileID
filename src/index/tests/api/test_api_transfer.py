from django.contrib.auth.models import User
from django.urls import reverse
from index.models import (
    Barcode,
    BarcodeUserProfile,
)
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class TransferDynamicBarcodeAPITest(APITestCase):
    """Tests for TransferDynamicBarcodeAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def _get_sample_html(self):
        """Return sample HTML that can be parsed"""
        return """
        <html>
        <h4 class="white-h4" style="margin-top: 10px;">John Doe</h4>
        <h4 id="student-id">12345</h4>
        <img src="data:image/jpeg;base64,dGVzdGltYWdl" />
        <script>
        var formattedTimestamp + "12345678901234"
        </script>
        </html>
        """

    def test_transfer_success(self):
        """Test successful HTML transfer and barcode creation"""
        self._auth(self.user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("barcode", response.data)

        # Check barcode was created
        barcode = Barcode.objects.get(barcode="12345678901234")
        self.assertEqual(barcode.user, self.user)
        self.assertEqual(barcode.barcode_type, "DynamicBarcode")

        # Check profile was created
        profile = BarcodeUserProfile.objects.get(linked_barcode=barcode)
        self.assertEqual(profile.name, "John Doe")
        self.assertEqual(profile.information_id, "12345")
        self.assertEqual(profile.user_profile_img, "dGVzdGltYWdl")

    def test_transfer_missing_html(self):
        """Test that missing HTML returns error"""
        self._auth(self.user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("html", response.data["errors"])

    def test_transfer_unparseable_html(self):
        """Test that unparseable HTML returns appropriate errors"""
        self._auth(self.user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": "<html><body>No barcode info here</body></html>"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        # Should have errors for missing fields
        errors = response.data["errors"]
        self.assertTrue(
            "barcode" in errors or "name" in errors or "information_id" in errors
        )

    def test_transfer_duplicate_barcode(self):
        """Test that transferring duplicate barcode fails"""
        self._auth(self.user)

        # Create existing barcode
        Barcode.objects.create(
            user=self.user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error can be in errors dict or at top level from serializer
        self.assertTrue("errors" in response.data or "barcode" in response.data)

    def test_transfer_unauthenticated(self):
        """Test that unauthenticated users cannot access endpoint"""
        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
