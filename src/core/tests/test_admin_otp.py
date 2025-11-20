from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models.admin_onetimepass import AdminOneTimePass

User = get_user_model()


class AdminOneTimePassTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testadmin", password="password")  # noqa: E501

    def test_otp_creation_and_validity(self):
        otp = AdminOneTimePass.objects.create(
            user=self.user,
            pass_code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertTrue(otp.is_valid())
        self.assertEqual(str(otp), f"OTP for {self.user} (Expires: {otp.expires_at})")  # noqa: E501

    def test_otp_expiration(self):
        otp = AdminOneTimePass.objects.create(
            user=self.user,
            pass_code="123456",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertFalse(otp.is_valid())

    def test_otp_usage(self):
        otp = AdminOneTimePass.objects.create(
            user=self.user,
            pass_code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        otp.is_used = True
        otp.save()
        self.assertFalse(otp.is_valid())
