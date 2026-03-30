from django.urls import reverse
from index.models import (
    Barcode,
    UserBarcodeSettings,
    UserBarcodePullSettings,
)
from rest_framework import status

from index.tests.api.test_api_dashboard_base import BarcodeDashboardTestBase


class BarcodeDashboardPullSettingsTest(BarcodeDashboardTestBase):
    """Test BarcodeDashboardAPIView — pull settings POST requests."""

    def test_dashboard_post_update_pull_settings(self):
        """Test updating pull settings via POST"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        data = {
            "pull_settings": {
                "pull_setting": "Enable",
                "gender_setting": "Male",
            }
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("pull_settings", response.data)
        self.assertEqual(response.data["pull_settings"]["pull_setting"], "Enable")
        self.assertEqual(response.data["pull_settings"]["gender_setting"], "Male")

        pull_settings = UserBarcodePullSettings.objects.get(user=self.user)
        self.assertEqual(pull_settings.pull_setting, "Enable")
        self.assertEqual(pull_settings.gender_setting, "Male")

    def test_dashboard_post_barcode_selection_disabled_when_pull_enabled(self):
        """Test that barcode selection is rejected when pull_setting is enabled"""  # noqa: E501
        self._authenticate_user(self.user)

        UserBarcodePullSettings.objects.create(
            user=self.user, pull_setting="Enable", gender_setting="Male"
        )

        barcode = Barcode.objects.create(
            user=self.user, barcode="12345678901234", barcode_type="DynamicBarcode"
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.post(url, {"barcode": barcode.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("barcode", response.data["errors"])

    def test_dashboard_post_can_update_barcode_when_pull_disabled(self):
        """Test that barcode can be updated when pull_setting is disabled"""
        self._authenticate_user(self.user)

        UserBarcodePullSettings.objects.create(
            user=self.user, pull_setting="Disable", gender_setting="Unknow"
        )

        barcode = Barcode.objects.create(
            user=self.user, barcode="12345678901234", barcode_type="DynamicBarcode"
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.post(url, {"barcode": barcode.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings = UserBarcodeSettings.objects.get(user=self.user)
        self.assertEqual(settings.barcode, barcode)

    def test_dashboard_post_auto_clear_barcode_when_pull_enabled(self):
        """Test that barcode is auto-cleared when pull_setting is enabled"""
        self._authenticate_user(self.user)

        barcode = Barcode.objects.create(
            user=self.user, barcode="12345678901234", barcode_type="DynamicBarcode"
        )
        settings = UserBarcodeSettings.objects.create(user=self.user, barcode=barcode)

        url = reverse("index:api_barcode_dashboard")
        data = {
            "pull_settings": {"pull_setting": "Enable", "gender_setting": "Male"},
            "barcode": barcode.id,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings.refresh_from_db()
        self.assertIsNone(settings.barcode)
        pull_settings = UserBarcodePullSettings.objects.get(user=self.user)
        self.assertEqual(pull_settings.pull_setting, "Enable")
