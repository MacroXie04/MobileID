from django.urls import reverse
from index.repositories import BarcodeRepository, SettingsRepository
from rest_framework import status

from index.api.tests.test_api_dashboard_base import BarcodeDashboardTestBase


class BarcodeDashboardWriteTest(BarcodeDashboardTestBase):
    """Test BarcodeDashboardAPIView -- POST, PUT, PATCH, DELETE requests."""

    def test_dashboard_post_update_settings(self):
        """Test updating barcode settings"""
        self._authenticate_user(self.user)

        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        data = {
            "barcode": barcode["barcode_uuid"],
            "associate_user_profile_with_barcode": False,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check settings were updated
        settings = SettingsRepository.get(self.user.id)
        self.assertEqual(settings["active_barcode_uuid"], barcode["barcode_uuid"])

    def test_dashboard_put_create_barcode(self):
        """Test creating new barcode"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": "newbarcode123456789"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")

        # Check barcode was created in DynamoDB
        barcode = BarcodeRepository.get_by_barcode_value("newbarcode123456789")
        self.assertIsNotNone(barcode)
        self.assertEqual(barcode["user_id"], str(self.user.id))
        self.assertEqual(barcode["barcode_type"], "Others")

    def test_dashboard_put_create_dynamic_barcode(self):
        """Test creating dynamic barcode (28 digits)"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": "1234567890123456789012345678"}  # 28 digits

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check barcode was created as dynamic with last 14 digits
        barcodes = BarcodeRepository.get_user_barcodes_by_type(
            self.user.id, "DynamicBarcode"
        )
        self.assertTrue(len(barcodes) > 0)
        barcode = barcodes[0]
        self.assertEqual(barcode["barcode"], "56789012345678")  # Last 14 digits

    def test_dashboard_delete_barcode(self):
        """Test deleting barcode"""
        self._authenticate_user(self.user)

        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="deleteme123456789",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": barcode["barcode_uuid"]}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check barcode was deleted
        deleted = BarcodeRepository.get_by_uuid(self.user.id, barcode["barcode_uuid"])
        self.assertIsNone(deleted)

    def test_dashboard_delete_barcode_not_found(self):
        """Test deleting non-existent barcode"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": "00000000-0000-0000-0000-000000099999"}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")

    def test_dashboard_patch_update_share_and_daily_limit(self):
        """Test PATCH to update share flag and daily usage limit"""
        self._authenticate_user(self.user)
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="patchbar12345678",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        # Update share_with_others using string truthy and set daily limit
        data = {
            "barcode_id": barcode["barcode_uuid"],
            "share_with_others": "true",
            "daily_usage_limit": 5,
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated = BarcodeRepository.get_by_uuid(self.user.id, barcode["barcode_uuid"])
        self.assertTrue(updated["share_with_others"])
        self.assertEqual(int(updated["daily_usage_limit"]), 5)

    def test_dashboard_patch_invalid_daily_limit(self):
        """Test PATCH with invalid daily limit values"""
        self._authenticate_user(self.user)
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="patchbarinvalid",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        # Negative number
        response = self.client.patch(
            url,
            {"barcode_id": barcode["barcode_uuid"], "daily_usage_limit": -1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Non-integer
        response = self.client.patch(
            url,
            {
                "barcode_id": barcode["barcode_uuid"],
                "daily_usage_limit": "not-a-number",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
