from django.urls import reverse
from index.repositories import BarcodeRepository, SettingsRepository
from rest_framework import status

from index.tests.api.test_api_dashboard_base import BarcodeDashboardTestBase


class BarcodeDashboardPullSettingsTest(BarcodeDashboardTestBase):
    """Test BarcodeDashboardAPIView -- pull settings POST requests."""

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

        settings = SettingsRepository.get(self.user.id)
        self.assertEqual(settings["pull_setting"], "Enable")
        self.assertEqual(settings["pull_gender_setting"], "Male")

    def test_dashboard_post_barcode_selection_disabled_when_pull_enabled(self):
        """Test that barcode selection is rejected when pull_setting is enabled"""
        self._authenticate_user(self.user)

        SettingsRepository.update(
            self.user.id,
            pull_setting="Enable",
            pull_gender_setting="Male",
        )

        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.post(
            url, {"barcode": barcode["barcode_uuid"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("barcode", response.data["errors"])

    def test_dashboard_post_can_update_barcode_when_pull_disabled(self):
        """Test that barcode can be updated when pull_setting is disabled"""
        self._authenticate_user(self.user)

        SettingsRepository.update(
            self.user.id,
            pull_setting="Disable",
            pull_gender_setting="Unknow",
        )

        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.post(
            url, {"barcode": barcode["barcode_uuid"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings = SettingsRepository.get(self.user.id)
        self.assertEqual(settings["active_barcode_uuid"], barcode["barcode_uuid"])

    def test_dashboard_post_auto_clear_barcode_when_pull_enabled(self):
        """Test that barcode is auto-cleared when pull_setting is enabled"""
        self._authenticate_user(self.user)

        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )
        SettingsRepository.update(
            self.user.id,
            active_barcode_uuid=barcode["barcode_uuid"],
        )

        url = reverse("index:api_barcode_dashboard")
        data = {
            "pull_settings": {"pull_setting": "Enable", "gender_setting": "Male"},
            "barcode": barcode["barcode_uuid"],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings = SettingsRepository.get(self.user.id)
        self.assertIsNone(settings.get("active_barcode_uuid"))
        self.assertEqual(settings["pull_setting"], "Enable")
