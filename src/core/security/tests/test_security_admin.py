"""
Tests for admin security — IP whitelist, session expiry, throttle, and audit logging.
"""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import AdminAuditLog


class AdminIPWhitelistTest(TestCase):
    """Test admin IP whitelist behavior"""

    @override_settings(ADMIN_ALLOWED_IPS=["127.0.0.1", "192.168.1.1"])
    def test_admin_ip_whitelist_blocks_unauthorized_ip(self):
        """Test that admin IP whitelist blocks unauthorized IPs"""
        client = Client(REMOTE_ADDR="10.0.0.1")
        response = client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 403)
        self.assertIn("Access denied", response.content.decode())

    @override_settings(ADMIN_ALLOWED_IPS=["127.0.0.1", "192.168.1.1"])
    def test_admin_ip_whitelist_allows_authorized_ip(self):
        """Test that admin IP whitelist allows authorized IPs"""
        staff_user = User.objects.create_user(
            username="staff", password="test123", is_staff=True
        )
        client = Client(REMOTE_ADDR="127.0.0.1")
        client.force_login(staff_user)

        response = client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    @override_settings(ADMIN_ALLOWED_IPS=[])
    def test_admin_ip_whitelist_disabled_when_empty(self):
        """Test that admin IP whitelist is disabled when empty list"""
        staff_user = User.objects.create_user(
            username="staff2", password="test123", is_staff=True
        )
        client = Client(REMOTE_ADDR="10.0.0.1")
        client.force_login(staff_user)

        response = client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)


class AdminAvailabilityTest(TestCase):
    """Test admin availability behavior in DynamoDB-only deployments."""

    @override_settings(PERSISTENCE_MODE="dynamodb")
    def test_admin_returns_service_unavailable_when_dynamodb_only(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("Django admin is unavailable", response.content.decode())

    @override_settings(PERSISTENCE_MODE="hybrid")
    def test_admin_login_page_available_when_sql_backing_present(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")


class AdminLoginThrottleTest(TestCase):
    """Test admin login throttle behavior"""

    @override_settings(
        REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"admin_login": "3/15min"}}
    )
    def test_admin_login_throttle_blocks_excessive_attempts(self):
        """Test that admin login throttling blocks excessive login attempts"""
        # Clear cache to ensure clean test
        cache.clear()

        client = Client(REMOTE_ADDR="127.0.0.1")
        admin_login_url = reverse("admin:login")

        # Make 3 attempts (should be allowed)
        for _ in range(3):
            response = client.post(
                admin_login_url,
                {"username": "test", "password": "wrong"},
            )
            self.assertNotEqual(response.status_code, 429)

        # 4th attempt should be throttled
        response = client.post(
            admin_login_url,
            {"username": "test", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn("Too many login attempts", response.content.decode())

    @override_settings(
        REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"admin_login": "5/15min"}}
    )
    def test_admin_login_throttle_allows_normal_usage(self):
        """Test that admin login throttling allows normal usage"""
        # Clear cache to ensure clean test
        cache.clear()

        client = Client(REMOTE_ADDR="127.0.0.1")
        admin_login_url = reverse("admin:login")

        # Make a few attempts (should be allowed)
        for _ in range(3):
            response = client.post(
                admin_login_url,
                {"username": "test", "password": "wrong"},
            )
            self.assertNotEqual(response.status_code, 429)


class AdminSessionExpiryTest(TestCase):
    """Test admin session expiry behavior"""

    @override_settings(ADMIN_SESSION_COOKIE_AGE=3600)
    def test_admin_session_expiry_set(self):
        """Test that admin session expiry is set correctly"""
        staff_user = User.objects.create_user(
            username="staff3", password="test123", is_staff=True
        )
        client = Client(REMOTE_ADDR="127.0.0.1")
        client.force_login(staff_user)

        # Access admin page
        response = client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

        # Check that session expiry is set (session should exist)
        self.assertTrue(client.session.session_key)
        # Session expiry should be set to ADMIN_SESSION_COOKIE_AGE (3600
        # seconds = 1 hour)
        expiry_age = client.session.get_expiry_age()
        # Expiry should be approximately 3600 seconds (within 5 seconds
        # tolerance)
        self.assertAlmostEqual(expiry_age, 3600, delta=5)


class AdminAuditLogTest(TestCase):
    """Test admin audit logging"""

    def test_admin_audit_log_created_on_post_action(self):
        """Test that admin audit log is created on POST actions"""
        # Clear existing logs
        AdminAuditLog.objects.all().delete()

        # Create staff user
        staff_user = User.objects.create_user(
            username="staff4",
            password="test123",
            is_staff=True,
            is_superuser=True,
        )
        client = Client(REMOTE_ADDR="127.0.0.1")
        client.force_login(staff_user)

        # Perform a POST action (like changing a user)
        # First create a test user to modify
        test_user = User.objects.create_user(username="testuser", password="test123")

        # POST to change the user (this should create an audit log)
        change_url = reverse("admin:auth_user_change", args=[test_user.id])
        response = client.post(
            change_url,
            {
                "username": "testuser",
                "email": "test@example.com",
                "is_active": "on",
                "_save": "Save",
            },
        )
        # Should redirect on success
        self.assertIn(response.status_code, [200, 302])

        # Check that audit log was created for the POST action
        logs = AdminAuditLog.objects.filter(
            user=staff_user, action=AdminAuditLog.CHANGE
        )
        self.assertGreaterEqual(logs.count(), 1)

    @override_settings(ADMIN_ALLOWED_IPS=[])
    def test_admin_audit_log_includes_ip_and_user_agent(self):
        """Test that admin audit log includes IP address and user agent"""
        # Clear existing logs
        AdminAuditLog.objects.all().delete()

        # Create staff user
        staff_user = User.objects.create_user(
            username="staff5",
            password="test123",
            is_staff=True,
            is_superuser=True,
        )
        client = Client(REMOTE_ADDR="192.168.1.100", HTTP_USER_AGENT="TestAgent/1.0")
        client.force_login(staff_user)

        # Perform a POST action to trigger audit logging
        test_user = User.objects.create_user(username="testuser2", password="test123")
        change_url = reverse("admin:auth_user_change", args=[test_user.id])
        client.post(
            change_url,
            {
                "username": "testuser2",
                "email": "test2@example.com",
                "is_active": "on",
                "_save": "Save",
            },
        )

        # Check audit log
        log = AdminAuditLog.objects.filter(user=staff_user).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, "192.168.1.100")
        self.assertIn("TestAgent", log.user_agent)
