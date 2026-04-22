"""Tests for the initadmin management command."""

from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

User = get_user_model()


class InitAdminCommandTest(TestCase):
    def _run(self):
        out = StringIO()
        call_command("initadmin", stdout=out)
        return out.getvalue()

    @patch.dict("os.environ", {}, clear=True)
    def test_warns_and_skips_when_env_vars_missing(self):
        output = self._run()

        self.assertIn("Missing DJANGO_SUPERUSER environment variables", output)
        self.assertFalse(User.objects.exists())

    @patch.dict(
        "os.environ",
        {
            "DJANGO_SUPERUSER_USERNAME": "root",
            "DJANGO_SUPERUSER_EMAIL": "",
            "DJANGO_SUPERUSER_PASSWORD": "pw",
        },
        clear=True,
    )
    def test_warns_when_email_empty(self):
        output = self._run()

        self.assertIn("Missing DJANGO_SUPERUSER environment variables", output)
        self.assertFalse(User.objects.exists())

    @patch.dict(
        "os.environ",
        {
            "DJANGO_SUPERUSER_USERNAME": "admin",
            "DJANGO_SUPERUSER_EMAIL": "admin@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "secret-pw-123",
        },
        clear=True,
    )
    def test_creates_new_superuser_with_expected_flags(self):
        output = self._run()

        self.assertIn("created successfully", output)
        user = User.objects.get(username="admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.check_password("secret-pw-123"))

    def test_updates_existing_superuser_credentials(self):
        original = User.objects.create_superuser(
            username="admin", email="old@example.com", password="old-pw"
        )

        with patch.dict(
            "os.environ",
            {
                "DJANGO_SUPERUSER_USERNAME": "admin",
                "DJANGO_SUPERUSER_EMAIL": "new@example.com",
                "DJANGO_SUPERUSER_PASSWORD": "new-pw-456",
            },
            clear=True,
        ):
            output = self._run()

        self.assertIn("already exists", output)
        user = User.objects.get(username="admin")
        self.assertEqual(user.pk, original.pk)
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("new-pw-456"))
        self.assertFalse(user.check_password("old-pw"))
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_promotes_existing_regular_user_to_superuser(self):
        User.objects.create_user(
            username="alice", email="alice@example.com", password="pw", is_active=False
        )

        with patch.dict(
            "os.environ",
            {
                "DJANGO_SUPERUSER_USERNAME": "alice",
                "DJANGO_SUPERUSER_EMAIL": "alice@example.com",
                "DJANGO_SUPERUSER_PASSWORD": "new-pw",
            },
            clear=True,
        ):
            self._run()

        alice = User.objects.get(username="alice")
        self.assertTrue(alice.is_superuser)
        self.assertTrue(alice.is_staff)
        self.assertTrue(alice.is_active)
