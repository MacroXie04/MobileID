from django.urls import reverse
from index.repositories import BarcodeRepository, SettingsRepository
from rest_framework import status

from index.api.tests.test_api_dashboard_base import BarcodeDashboardTestBase


class BarcodeDashboardReadTest(BarcodeDashboardTestBase):
    """Test BarcodeDashboardAPIView -- GET requests and field states."""

    def test_dashboard_get(self):
        """Test getting dashboard data"""
        self._authenticate_user(self.user)

        # Create some barcodes
        BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )
        BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="static123456789",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("settings", response.data)
        self.assertIn("barcodes", response.data)

        # Should have 2 barcodes
        self.assertEqual(len(response.data["barcodes"]), 2)

    def test_dashboard_get_includes_pull_settings(self):
        """Test that GET dashboard includes pull_settings in response"""
        self._authenticate_user(self.user)

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("pull_settings", response.data)
        self.assertEqual(response.data["pull_settings"]["pull_setting"], "Disable")
        self.assertEqual(response.data["pull_settings"]["gender_setting"], "Unknow")

    def test_dashboard_get_field_states_barcode_disabled_when_pull_enabled(
        self,
    ):
        """Test that field_states shows barcode_disabled when pull_setting is enabled"""
        self._authenticate_user(self.user)

        # Enable pull setting via SettingsRepository
        SettingsRepository.update(
            self.user.id,
            pull_setting="Enable",
            pull_gender_setting="Female",
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        field_states = response.data["settings"]["field_states"]
        self.assertTrue(field_states["barcode_disabled"])

    def test_dashboard_get_field_states_barcode_enabled_when_pull_disabled(
        self,
    ):
        """field_states barcode_disabled=False when pull disabled"""
        self._authenticate_user(self.user)

        # Ensure pull setting is disabled via SettingsRepository
        SettingsRepository.update(
            self.user.id,
            pull_setting="Disable",
            pull_gender_setting="Unknow",
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        field_states = response.data["settings"]["field_states"]
        self.assertFalse(field_states["barcode_disabled"])
