from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import AdminAuditLog, AdminOneTimePass


class AdminAuditLogModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="audituser", password="pass123")

    def test_create_audit_log_entry(self):
        log = AdminAuditLog.objects.create(
            user=self.user,
            ip_address="192.168.1.1",
            action=AdminAuditLog.LOGIN,
            resource="admin",
            success=True,
            user_agent="TestAgent/1.0",
            details={"method": "POST"},
        )
        log.refresh_from_db()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.ip_address, "192.168.1.1")
        self.assertEqual(log.action, "login")
        self.assertTrue(log.success)
        self.assertEqual(log.details, {"method": "POST"})

    def test_str_representation(self):
        log = AdminAuditLog.objects.create(
            user=self.user,
            action=AdminAuditLog.VIEW,
            resource="dashboard",
        )
        result = str(log)
        self.assertIn("audituser", result)
        self.assertIn("view", result)
        self.assertIn("dashboard", result)

    def test_str_with_no_user(self):
        log = AdminAuditLog.objects.create(
            user=None,
            action=AdminAuditLog.LOGIN,
            resource="admin",
            success=False,
        )
        self.assertIn("anonymous", str(log))

    def test_ordering_by_timestamp_desc(self):
        log1 = AdminAuditLog.objects.create(
            user=self.user, action=AdminAuditLog.VIEW, resource="page1"
        )
        log2 = AdminAuditLog.objects.create(
            user=self.user, action=AdminAuditLog.VIEW, resource="page2"
        )
        logs = list(AdminAuditLog.objects.all())
        # Most recent first
        self.assertEqual(logs[0].id, log2.id)
        self.assertEqual(logs[1].id, log1.id)

    def test_all_action_choices_valid(self):
        valid_actions = [choice[0] for choice in AdminAuditLog.ACTION_CHOICES]
        self.assertEqual(len(valid_actions), 7)
        for action in valid_actions:
            log = AdminAuditLog.objects.create(
                user=self.user, action=action, resource="test"
            )
            log.full_clean()  # Should not raise

    def test_json_details_field(self):
        details = {"key": "value", "nested": {"a": 1}, "list": [1, 2, 3]}
        log = AdminAuditLog.objects.create(
            user=self.user,
            action=AdminAuditLog.ACTION,
            resource="test",
            details=details,
        )
        log.refresh_from_db()
        self.assertEqual(log.details, details)


class AdminOneTimePassEdgeCaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="otpuser", password="pass123")

    def test_otp_is_valid_returns_false_when_used_and_expired(self):
        otp = AdminOneTimePass.objects.create(
            user=self.user,
            pass_code="123456",
            expires_at=timezone.now() - timedelta(minutes=5),
            is_used=True,
        )
        self.assertFalse(otp.is_valid())

    def test_otp_exactly_at_expiry_boundary(self):
        """expires_at == now() should return False (strict < comparison)."""
        now = timezone.now()
        otp = AdminOneTimePass.objects.create(
            user=self.user,
            pass_code="654321",
            expires_at=now,
        )
        with patch("django.utils.timezone.now", return_value=now):
            self.assertFalse(otp.is_valid())
