from django.urls import reverse
from index.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
)
from rest_framework import status

from index.tests.api.test_api_dashboard_base import BarcodeDashboardTestBase


class BarcodeDashboardWriteTest(BarcodeDashboardTestBase):
    """Test BarcodeDashboardAPIView — POST, PUT, PATCH, DELETE requests."""

    def test_dashboard_post_update_settings(self):
        """Test updating barcode settings"""
        self._authenticate_user(self.user)

        barcode = Barcode.objects.create(
            user=self.user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {
            "barcode": barcode.id,
            "associate_user_profile_with_barcode": False,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check settings were updated
        settings = UserBarcodeSettings.objects.get(user=self.user)
        self.assertEqual(settings.barcode, barcode)

    def test_dashboard_put_create_barcode(self):
        """Test creating new barcode"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": "newbarcode123456789"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")

        # Check barcode was created
        barcode = Barcode.objects.get(barcode="newbarcode123456789")
        self.assertEqual(barcode.user, self.user)
        self.assertEqual(barcode.barcode_type, "Others")

    def test_dashboard_put_create_dynamic_barcode(self):
        """Test creating dynamic barcode (28 digits)"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": "1234567890123456789012345678"}  # 28 digits

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check barcode was created as dynamic with last 14 digits
        barcode = Barcode.objects.get(user=self.user, barcode_type="DynamicBarcode")
        self.assertEqual(barcode.barcode, "56789012345678")  # Last 14 digits

    def test_dashboard_delete_barcode(self):
        """Test deleting barcode"""
        self._authenticate_user(self.user)

        barcode = Barcode.objects.create(
            user=self.user,
            barcode="deleteme123456789",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": barcode.id}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check barcode was deleted
        self.assertFalse(Barcode.objects.filter(id=barcode.id).exists())

    def test_dashboard_delete_barcode_not_found(self):
        """Test deleting non-existent barcode"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": 99999}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")

    def test_dashboard_patch_update_share_and_daily_limit(self):
        """Test PATCH to update share flag and daily usage limit"""
        self._authenticate_user(self.user)
        barcode = Barcode.objects.create(
            user=self.user,
            barcode="patchbar12345678",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        # Update share_with_others using string truthy and set daily limit
        data = {
            "barcode_id": barcode.id,
            "share_with_others": "true",
            "daily_usage_limit": 5,
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        barcode.refresh_from_db()
        self.assertTrue(barcode.share_with_others)
        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.daily_usage_limit, 5)

    def test_dashboard_patch_invalid_daily_limit(self):
        """Test PATCH with invalid daily limit values"""
        self._authenticate_user(self.user)
        barcode = Barcode.objects.create(
            user=self.user,
            barcode="patchbarinvalid",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        # Negative number
        response = self.client.patch(
            url,
            {"barcode_id": barcode.id, "daily_usage_limit": -1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Non-integer
        response = self.client.patch(
            url,
            {"barcode_id": barcode.id, "daily_usage_limit": "not-a-number"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_delete_identification_barcode_forbidden(self):
        """Test that identification barcodes cannot be deleted"""
        self._authenticate_user(self.user)

        barcode = Barcode.objects.create(
            user=self.user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": barcode.id}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
