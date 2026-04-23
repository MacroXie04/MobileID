"""
Unit tests for SecurityRepository — DynamoDB-backed auth security operations.

Covers:
- AccessTokenBlacklist: is_blacklisted, blacklist_token, check_session_revocation
- FailedLoginAttempt: get_failed_attempt, increment_failed_attempt, reset, lock
- LoginAuditLog: create_audit_log, get_audit_logs_for_user

These methods are called on the hot path of every authenticated request, so
their contract (return shape, lock threshold, most-recent-first ordering) is
worth pinning down explicitly.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from authn.repositories import SecurityRepository
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin


class BlacklistOperationsTests(DynamoDBCleanupMixin, TestCase):
    def test_is_blacklisted_returns_false_for_unknown_jti(self):
        self.assertFalse(SecurityRepository.is_blacklisted("nonexistent-jti"))

    def test_is_blacklisted_returns_true_after_blacklist(self):
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_token("jti-abc-123", user_id=42, expires_at=expires)
        self.assertTrue(SecurityRepository.is_blacklisted("jti-abc-123"))

    def test_blacklist_token_is_idempotent(self):
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_token("jti-dup", user_id=1, expires_at=expires)
        SecurityRepository.blacklist_token("jti-dup", user_id=1, expires_at=expires)
        self.assertTrue(SecurityRepository.is_blacklisted("jti-dup"))

    def test_blacklist_session_uses_session_key_as_jti(self):
        """blacklist_session delegates to blacklist_token with the session key."""
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_session(
            user_id=7, session_key="session_7_1700000000", expires_at=expires
        )
        self.assertTrue(SecurityRepository.is_blacklisted("session_7_1700000000"))


class SessionRevocationTests(DynamoDBCleanupMixin, TestCase):
    """check_session_revocation scans a narrow window of JTIs around token iat."""

    def test_returns_false_when_no_sessions_blacklisted(self):
        self.assertFalse(
            SecurityRepository.check_session_revocation(user_id=1, token_iat=1700000000)
        )

    def test_returns_true_when_exact_iat_session_blacklisted(self):
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_token(
            "session_1_1700000000", user_id=1, expires_at=expires
        )
        self.assertTrue(
            SecurityRepository.check_session_revocation(user_id=1, token_iat=1700000000)
        )

    def test_returns_true_when_session_within_window(self):
        """A session blacklisted at iat-1 should still match when checking iat."""
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_token(
            "session_1_1699999999", user_id=1, expires_at=expires
        )
        self.assertTrue(
            SecurityRepository.check_session_revocation(user_id=1, token_iat=1700000000)
        )

    def test_returns_false_when_session_outside_window(self):
        """A session far from the iat is not considered the same session."""
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_token(
            "session_1_1700001000", user_id=1, expires_at=expires
        )
        self.assertFalse(
            SecurityRepository.check_session_revocation(
                user_id=1, token_iat=1700000000, window=2
            )
        )

    def test_different_user_does_not_match(self):
        """Session keys are namespaced by user_id."""
        expires = timezone.now() + timedelta(hours=1)
        SecurityRepository.blacklist_token(
            "session_1_1700000000", user_id=1, expires_at=expires
        )
        self.assertFalse(
            SecurityRepository.check_session_revocation(user_id=2, token_iat=1700000000)
        )


class FailedLoginAttemptTests(DynamoDBCleanupMixin, TestCase):
    def test_get_failed_attempt_returns_none_when_missing(self):
        self.assertIsNone(SecurityRepository.get_failed_attempt("nobody"))

    def test_increment_creates_new_record_on_first_attempt(self):
        item = SecurityRepository.increment_failed_attempt("alice", ip_address="10.0.0.1")
        self.assertEqual(int(item["attempt_count"]), 1)
        self.assertEqual(item["username"], "alice")
        self.assertEqual(item["ip_address"], "10.0.0.1")
        self.assertNotIn("locked_until", item)

    def test_increment_increments_existing_record(self):
        SecurityRepository.increment_failed_attempt("alice")
        SecurityRepository.increment_failed_attempt("alice")
        item = SecurityRepository.get_failed_attempt("alice")
        self.assertEqual(int(item["attempt_count"]), 2)

    def test_increment_locks_account_at_threshold(self):
        """Default max_attempts is 5. The 5th call should set locked_until."""
        for _ in range(4):
            SecurityRepository.increment_failed_attempt("alice")
        self.assertIsNone(
            SecurityRepository.get_failed_attempt("alice").get("locked_until")
        )

        SecurityRepository.increment_failed_attempt("alice")
        item = SecurityRepository.get_failed_attempt("alice")
        self.assertEqual(int(item["attempt_count"]), 5)
        self.assertIsNotNone(item.get("locked_until"))

    def test_increment_respects_custom_threshold(self):
        item = SecurityRepository.increment_failed_attempt(
            "alice", max_attempts=1, lockout_duration=timedelta(minutes=5)
        )
        self.assertIsNotNone(item.get("locked_until"))

    def test_increment_does_not_relock_already_locked_account(self):
        """Once locked, subsequent increments don't bump locked_until forward."""
        for _ in range(5):
            SecurityRepository.increment_failed_attempt("alice")
        original_locked_until = SecurityRepository.get_failed_attempt("alice")[
            "locked_until"
        ]

        SecurityRepository.increment_failed_attempt("alice")
        item = SecurityRepository.get_failed_attempt("alice")
        self.assertEqual(item["locked_until"], original_locked_until)

    def test_reset_failed_attempts_zeroes_counter(self):
        SecurityRepository.increment_failed_attempt("alice")
        SecurityRepository.increment_failed_attempt("alice")
        SecurityRepository.reset_failed_attempts("alice", ip_address="10.0.0.2")
        item = SecurityRepository.get_failed_attempt("alice")
        self.assertEqual(int(item["attempt_count"]), 0)
        self.assertEqual(item["ip_address"], "10.0.0.2")

    def test_is_account_locked_false_when_no_record(self):
        self.assertFalse(SecurityRepository.is_account_locked("ghost"))

    def test_is_account_locked_false_when_no_locked_until(self):
        SecurityRepository.increment_failed_attempt("alice")
        self.assertFalse(SecurityRepository.is_account_locked("alice"))

    def test_is_account_locked_true_when_locked_until_in_future(self):
        for _ in range(5):
            SecurityRepository.increment_failed_attempt("alice")
        self.assertTrue(SecurityRepository.is_account_locked("alice"))

    def test_is_account_locked_false_when_locked_until_in_past(self):
        """After the lockout duration passes, the account is no longer locked."""
        SecurityRepository.increment_failed_attempt(
            "alice", max_attempts=1, lockout_duration=timedelta(seconds=-10)
        )
        self.assertFalse(SecurityRepository.is_account_locked("alice"))


class LoginAuditLogTests(DynamoDBCleanupMixin, TestCase):
    def test_create_audit_log_writes_minimal_entry(self):
        item = SecurityRepository.create_audit_log(username="alice", success=True)
        self.assertEqual(item["username"], "alice")
        self.assertTrue(item["success"])
        self.assertIn("created_at", item)

    def test_create_audit_log_writes_all_fields_when_provided(self):
        item = SecurityRepository.create_audit_log(
            username="alice",
            user_id=42,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
            result="success",
            reason="valid credentials",
            success=True,
        )
        self.assertEqual(item["user_id"], "42")
        self.assertEqual(item["ip_address"], "10.0.0.1")
        self.assertEqual(item["user_agent"], "Mozilla/5.0")
        self.assertEqual(item["result"], "success")
        self.assertEqual(item["reason"], "valid credentials")

    def test_create_audit_log_omits_empty_optional_fields(self):
        item = SecurityRepository.create_audit_log(username="alice", success=False)
        for omitted in ("user_id", "ip_address", "user_agent", "result", "reason"):
            self.assertNotIn(omitted, item)

    def test_get_audit_logs_returns_empty_for_unknown_user(self):
        self.assertEqual(SecurityRepository.get_audit_logs_for_user("ghost"), [])

    def test_get_audit_logs_returns_most_recent_first(self):
        SecurityRepository.create_audit_log(username="alice", success=True, reason="one")
        SecurityRepository.create_audit_log(username="alice", success=True, reason="two")
        SecurityRepository.create_audit_log(username="alice", success=True, reason="three")

        logs = SecurityRepository.get_audit_logs_for_user("alice")
        self.assertEqual(len(logs), 3)
        # ScanIndexForward=False means descending by sk (LOG#<created_at>#<uuid>),
        # so the last created entry should be first.
        self.assertEqual(logs[0]["reason"], "three")
        self.assertEqual(logs[-1]["reason"], "one")

    def test_get_audit_logs_respects_limit(self):
        for i in range(5):
            SecurityRepository.create_audit_log(username="alice", reason=f"attempt-{i}")
        logs = SecurityRepository.get_audit_logs_for_user("alice", limit=2)
        self.assertEqual(len(logs), 2)

    def test_get_audit_logs_isolates_by_username(self):
        SecurityRepository.create_audit_log(username="alice", success=True)
        SecurityRepository.create_audit_log(username="bob", success=True)
        self.assertEqual(len(SecurityRepository.get_audit_logs_for_user("alice")), 1)
        self.assertEqual(len(SecurityRepository.get_audit_logs_for_user("bob")), 1)
