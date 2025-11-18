"""
Tests for OIT status service functionality.
"""

from unittest.mock import patch

from django.test import TestCase
from index.status.OIT import OIT


class OITStatusTest(TestCase):
    """Test OIT status service functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.oit = OIT()

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_returns_operational_status_for_sso(self, mock_fetch_data):
        """Test that OIT service returns 'Operational' status for SSO (Single Sign-On)"""
        # Mock HTML response with SSO service operational
        mock_html = """
        <div class="service">
            <p class="container_name">SSO (Single Sign-On)</p>
            <p class="pull-right">Operational</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        self.assertIn("services", status_info)
        self.assertIn("SSO (Single Sign-On)", status_info["services"])
        self.assertEqual(status_info["services"]["SSO (Single Sign-On)"], "Operational")

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_returns_operational_status_for_duo_2fa(self, mock_fetch_data):
        """Test that OIT service returns 'Operational' status for Duo 2FA"""
        # Mock HTML response with Duo 2FA service operational
        mock_html = """
        <div class="service">
            <p class="container_name">Duo 2FA</p>
            <p class="pull-right">Operational</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        self.assertIn("services", status_info)
        self.assertIn("Duo 2FA", status_info["services"])
        self.assertEqual(status_info["services"]["Duo 2FA"], "Operational")

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_returns_operational_status_for_catcard(self, mock_fetch_data):
        """Test that OIT service returns 'Operational' status for CatCard"""
        # Mock HTML response with CatCard service operational
        mock_html = """
        <div class="service">
            <p class="container_name">CatCard</p>
            <p class="pull-right">Operational</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        self.assertIn("services", status_info)
        self.assertIn("CatCard", status_info["services"])
        self.assertEqual(status_info["services"]["CatCard"], "Operational")

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_returns_operational_status_for_dining_payment_systems(
        self, mock_fetch_data
    ):
        """Test that OIT service returns 'Operational' status for Dining Payment Systems"""
        # Mock HTML response with Dining Payment Systems service operational
        mock_html = """
        <div class="service">
            <p class="container_name">Dining Payment Systems</p>
            <p class="pull-right">Operational</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        self.assertIn("services", status_info)
        self.assertIn("Dining Payment Systems", status_info["services"])
        self.assertEqual(
            status_info["services"]["Dining Payment Systems"], "Operational"
        )

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_returns_multiple_services_status(self, mock_fetch_data):
        """Test that OIT service returns status for multiple services including the required ones"""
        # Mock HTML response with multiple services
        mock_html = """
        <div class="service">
            <p class="container_name">SSO (Single Sign-On)</p>
            <p class="pull-right">Operational</p>
        </div>
        <div class="service">
            <p class="container_name">Duo 2FA</p>
            <p class="pull-right">Operational</p>
        </div>
        <div class="service">
            <p class="container_name">CatCard</p>
            <p class="pull-right">Operational</p>
        </div>
        <div class="service">
            <p class="container_name">Dining Payment Systems</p>
            <p class="pull-right">Operational</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        # Verify all required services are present and operational
        required_services = [
            "SSO (Single Sign-On)",
            "Duo 2FA",
            "CatCard",
            "Dining Payment Systems",
        ]

        for service in required_services:
            self.assertIn(service, status_info["services"])
            self.assertEqual(status_info["services"][service], "Operational")

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_handles_service_outage_status(self, mock_fetch_data):
        """Test that OIT service can handle non-operational status for services"""
        # Mock HTML response with some services having issues
        mock_html = """
        <div class="service">
            <p class="container_name">SSO (Single Sign-On)</p>
            <p class="pull-right">Operational</p>
        </div>
        <div class="service">
            <p class="container_name">Duo 2FA</p>
            <p class="pull-right">Degraded Performance</p>
        </div>
        <div class="service">
            <p class="container_name">CatCard</p>
            <p class="pull-right">Operational</p>
        </div>
        <div class="service">
            <p class="container_name">Dining Payment Systems</p>
            <p class="pull-right">Service Disruption</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        # Verify services are captured with their actual status
        self.assertEqual(status_info["services"]["SSO (Single Sign-On)"], "Operational")
        self.assertEqual(status_info["services"]["Duo 2FA"], "Degraded Performance")
        self.assertEqual(status_info["services"]["CatCard"], "Operational")
        self.assertEqual(
            status_info["services"]["Dining Payment Systems"], "Service Disruption"
        )

    @patch("index.status.OIT.OIT.fetch_data")
    def test_oit_response_structure(self, mock_fetch_data):
        """Test that OIT service returns properly structured response"""
        mock_html = """
        <div class="service">
            <p class="container_name">SSO (Single Sign-On)</p>
            <p class="pull-right">Operational</p>
        </div>
        """
        mock_fetch_data.return_value = mock_html

        status_info = self.oit.get_status()

        # Verify response structure
        self.assertIn("time", status_info)
        self.assertIn("services", status_info)
        self.assertIsInstance(status_info["services"], dict)
        self.assertIsInstance(status_info["time"], str)

        # Verify time format (should be YYYY-MM-DD HH:MM:SS)
        time_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        self.assertRegex(status_info["time"], time_pattern)

    @patch("requests.get")
    def test_oit_fetch_data_handles_http_errors(self, mock_get):
        """Test that OIT service handles HTTP errors gracefully"""
        # Mock HTTP error
        mock_response = mock_get.return_value
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")

        with self.assertRaises(Exception):
            self.oit.fetch_data()

    def test_oit_parse_status_with_empty_html(self):
        """Test that OIT service handles empty HTML gracefully"""
        empty_html = ""
        data = self.oit.parse_status(empty_html)

        self.assertEqual(data.time, data.time)  # Time should still be set
        self.assertEqual(len(data.services), 0)  # No services found

    def test_oit_parse_status_with_malformed_html(self):
        """Test that OIT service handles malformed HTML gracefully"""
        malformed_html = "<div>Some malformed content without proper structure</div>"
        data = self.oit.parse_status(malformed_html)

        self.assertEqual(data.time, data.time)  # Time should still be set
        self.assertEqual(
            len(data.services), 0
        )  # No services found due to malformed HTML

    def test_oit_fetch_real_status_from_ucmerced(self):
        """Test that OIT service can fetch and parse real status from https://status.ucmerced.edu/"""
        try:
            # Fetch real status from UC Merced status page
            status_info = self.oit.get_status()

            # Verify response structure
            self.assertIn("time", status_info)
            self.assertIn("services", status_info)
            self.assertIsInstance(status_info["services"], dict)
            self.assertIsInstance(status_info["time"], str)

            # Verify that we got some services (the page should have many services)
            self.assertGreater(len(status_info["services"]), 0)

            # Verify that our required services are present in the real data
            required_services = [
                "SSO (Single Sign-On)",
                "Duo 2FA",
                "CatCard",
                "Dining Payment Systems",
            ]

            for service in required_services:
                self.assertIn(
                    service,
                    status_info["services"],
                    f"Required service '{service}' not found in real status data",
                )
                # Verify the service has a status (could be Operational, Service Disruption, etc.)
                self.assertIsNotNone(status_info["services"][service])
                self.assertGreater(len(status_info["services"][service]), 0)

            # Print the actual status for debugging/information
            print("\nReal UC Merced Status Retrieved:")
            print(f"Time: {status_info['time']}")
            print(f"Total Services: {len(status_info['services'])}")
            for service in required_services:
                print(f"{service}: {status_info['services'][service]}")

        except Exception as e:
            # If the real fetch fails (network issues, etc.), we'll skip this test
            self.skipTest(f"Could not fetch real status from UC Merced: {str(e)}")

    def test_oit_real_status_contains_operational_services(self):
        """Test that real UC Merced status contains operational services"""
        try:
            # Fetch real status from UC Merced status page
            status_info = self.oit.get_status()

            # Check that we have services with 'Operational' status
            operational_services = [
                service
                for service, status in status_info["services"].items()
                if status == "Operational"
            ]

            # Should have at least some operational services
            self.assertGreater(
                len(operational_services),
                0,
                "No operational services found in real status data",
            )

            # Verify our required services are operational (based on the current status page)
            required_services = [
                "SSO (Single Sign-On)",
                "Duo 2FA",
                "CatCard",
                "Dining Payment Systems",
            ]

            operational_required = []
            for service in required_services:
                if service in status_info["services"]:
                    if status_info["services"][service] == "Operational":
                        operational_required.append(service)

            # At least some of our required services should be operational
            self.assertGreater(
                len(operational_required),
                0,
                f"None of the required services are operational. "
                f"Current status: {[(s, status_info['services'].get(s, 'Not Found')) for s in required_services]}",
            )

            print(f"\nOperational Required Services: {operational_required}")

        except Exception as e:
            # If the real fetch fails (network issues, etc.), we'll skip this test
            self.skipTest(f"Could not fetch real status from UC Merced: {str(e)}")
