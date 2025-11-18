"""
Tests for health check endpoint.
"""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class HealthCheckTest(TestCase):
    """Test health check endpoint"""

    def test_health_check_get_returns_200(self):
        """Test that health check endpoint returns 200 OK for GET request"""
        url = reverse("health_check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_health_check_head_returns_200(self):
        """Test that health check endpoint returns 200 OK for HEAD request"""
        url = reverse("health_check")
        response = self.client.head(url)

        self.assertEqual(response.status_code, 200)

    def test_health_check_response_structure(self):
        """Test that health check response has correct structure"""
        url = reverse("health_check")
        response = self.client.get(url)

        data = response.json()
        self.assertIn("status", data)
        self.assertIn("service", data)
        self.assertIn("database", data)

        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "MobileID")
        self.assertEqual(data["database"], "connected")

    def test_health_check_post_not_allowed(self):
        """Test that health check endpoint does not accept POST requests"""
        url = reverse("health_check")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_health_check_database_connectivity(self):
        """Test that health check verifies database connectivity"""
        url = reverse("health_check")
        response = self.client.get(url)

        data = response.json()
        # In test environment, database should be connected
        self.assertEqual(data["database"], "connected")

    @patch("django.db.connection.cursor")
    def test_health_check_database_failure(self, mock_cursor):
        """Test health check response when database is unavailable"""
        # Mock database connection failure
        mock_cursor.side_effect = Exception("Database connection failed")

        url = reverse("health_check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["database"], "disconnected")
        self.assertIn("error", data)
