from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from authn.models import AccessTokenBlacklist


class AccessTokenBlacklistModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="blacklist_user", password="pass123"
        )

    def test_blacklist_token_creates_entry(self):
        expires = timezone.now() + timedelta(hours=1)
        AccessTokenBlacklist.blacklist_token("jti-abc-123", self.user, expires)
        self.assertTrue(AccessTokenBlacklist.objects.filter(jti="jti-abc-123").exists())
        entry = AccessTokenBlacklist.objects.get(jti="jti-abc-123")
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.expires_at, expires)

    def test_blacklist_token_idempotent(self):
        expires = timezone.now() + timedelta(hours=1)
        AccessTokenBlacklist.blacklist_token("jti-idem", self.user, expires)
        AccessTokenBlacklist.blacklist_token("jti-idem", self.user, expires)
        self.assertEqual(AccessTokenBlacklist.objects.filter(jti="jti-idem").count(), 1)

    def test_is_blacklisted_returns_true(self):
        AccessTokenBlacklist.objects.create(
            jti="jti-blocked",
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertTrue(AccessTokenBlacklist.is_blacklisted("jti-blocked"))

    def test_is_blacklisted_returns_false_for_unknown(self):
        self.assertFalse(AccessTokenBlacklist.is_blacklisted("nonexistent-jti"))

    def test_cleanup_expired_removes_old_entries(self):
        AccessTokenBlacklist.objects.create(
            jti="jti-expired",
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        deleted_count, _ = AccessTokenBlacklist.cleanup_expired()
        self.assertEqual(deleted_count, 1)
        self.assertFalse(
            AccessTokenBlacklist.objects.filter(jti="jti-expired").exists()
        )

    def test_cleanup_expired_preserves_active_entries(self):
        AccessTokenBlacklist.objects.create(
            jti="jti-active",
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        AccessTokenBlacklist.cleanup_expired()
        self.assertTrue(AccessTokenBlacklist.objects.filter(jti="jti-active").exists())

    def test_str_representation(self):
        entry = AccessTokenBlacklist.objects.create(
            jti="abcdefghijklmnopqrstuvwxyz",
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertIn("abcdefghijklmnopqrst", str(entry))
        self.assertIn(str(self.user.id), str(entry))
