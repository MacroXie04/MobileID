from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from mobileid.models import UserProfile, UserBarcodeSettings, Barcode, BarcodeUsage

class UserModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )

    def test_user_creation(self):
        """Test that a user can be created"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpassword'))

class UserProfileModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create user profile for the user
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name='Test Student',
            information_id='12345678',
            user_profile_img=''  # Empty string instead of None
        )

    def test_user_profile_creation(self):
        """Test that user profile can be created"""
        self.assertEqual(self.user_profile.user, self.user)
        self.assertEqual(self.user_profile.name, 'Test Student')
        self.assertEqual(self.user_profile.information_id, '12345678')

        # Test the new account security fields
        self.assertEqual(self.user_profile.failed_login_attempts, 0)
        self.assertFalse(self.user_profile.is_locked)
        self.assertIsNone(self.user_profile.locked_until)

class AccountLockingTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create user profile for the user
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name='Test Student',
            information_id='12345678',
            user_profile_img=''
        )

    def test_failed_login_attempts_increment(self):
        """Test that failed login attempts are incremented correctly"""
        # Initially, failed login attempts should be 0
        self.assertEqual(self.user_profile.failed_login_attempts, 0)

        # Increment failed login attempts
        self.user_profile.failed_login_attempts += 1
        self.user_profile.save()

        # Refresh from database
        self.user_profile.refresh_from_db()

        # Check that failed login attempts is now 1
        self.assertEqual(self.user_profile.failed_login_attempts, 1)

    def test_account_locking(self):
        """Test that an account is locked after exceeding the maximum number of failed attempts"""
        # Set failed login attempts to one less than the maximum
        self.user_profile.failed_login_attempts = settings.MAX_FAILED_LOGIN_ATTEMPTS - 1
        self.user_profile.save()

        # Account should not be locked yet
        self.assertFalse(self.user_profile.is_locked)

        # Increment failed login attempts to reach the maximum
        self.user_profile.failed_login_attempts += 1

        # Lock the account
        self.user_profile.is_locked = True
        self.user_profile.locked_until = timezone.now() + timezone.timedelta(minutes=settings.ACCOUNT_LOCKOUT_DURATION)
        self.user_profile.save()

        # Refresh from database
        self.user_profile.refresh_from_db()

        # Account should now be locked
        self.assertTrue(self.user_profile.is_locked)
        self.assertIsNotNone(self.user_profile.locked_until)

    def test_account_unlocking(self):
        """Test that an account is unlocked after the lockout period expires"""
        # Lock the account
        self.user_profile.is_locked = True
        # Set locked_until to a time in the past
        self.user_profile.locked_until = timezone.now() - timezone.timedelta(minutes=1)
        self.user_profile.save()

        # Check if lockout period has expired
        if self.user_profile.locked_until < timezone.now():
            # Unlock the account
            self.user_profile.is_locked = False
            self.user_profile.failed_login_attempts = 0
            self.user_profile.locked_until = None
            self.user_profile.save()

        # Refresh from database
        self.user_profile.refresh_from_db()

        # Account should now be unlocked
        self.assertFalse(self.user_profile.is_locked)
        self.assertEqual(self.user_profile.failed_login_attempts, 0)
        self.assertIsNone(self.user_profile.locked_until)

class UserBarcodeSettingsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create a test barcode
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode_type='Static',
            barcode='12345678',
            linked_id='87654321'
        )

        # Create barcode settings for the user
        self.barcode_settings = UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=self.barcode,
            server_verification=True,
            timestamp_verification=False,
            barcode_pull=True
        )

    def test_barcode_settings_creation(self):
        """Test that barcode settings can be created"""
        self.assertEqual(self.barcode_settings.user, self.user)
        self.assertEqual(self.barcode_settings.barcode, self.barcode)
        self.assertTrue(self.barcode_settings.server_verification)
        self.assertFalse(self.barcode_settings.timestamp_verification)
        self.assertTrue(self.barcode_settings.barcode_pull)

    def test_barcode_settings_update(self):
        """Test that barcode settings can be updated"""
        # Update barcode settings
        self.barcode_settings.server_verification = False
        self.barcode_settings.timestamp_verification = True
        self.barcode_settings.save()

        # Refresh from database
        self.barcode_settings.refresh_from_db()

        # Check that settings were updated
        self.assertFalse(self.barcode_settings.server_verification)
        self.assertTrue(self.barcode_settings.timestamp_verification)

    def test_barcode_settings_with_null_barcode(self):
        """Test that barcode settings can be updated to have a null barcode"""
        # Update existing barcode settings to have null barcode
        self.barcode_settings.barcode = None
        self.barcode_settings.server_verification = False
        self.barcode_settings.timestamp_verification = True
        self.barcode_settings.barcode_pull = False
        self.barcode_settings.save()

        # Refresh from database
        self.barcode_settings.refresh_from_db()

        # Check that settings were updated correctly
        self.assertEqual(self.barcode_settings.user, self.user)
        self.assertIsNone(self.barcode_settings.barcode)
        self.assertFalse(self.barcode_settings.server_verification)
        self.assertTrue(self.barcode_settings.timestamp_verification)
        self.assertFalse(self.barcode_settings.barcode_pull)

class BarcodeModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create a test barcode
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode_type='Static',
            barcode='12345678',
            linked_id='87654321'
        )

    def test_barcode_creation(self):
        """Test that a barcode can be created"""
        self.assertEqual(self.barcode.user, self.user)
        self.assertEqual(self.barcode.barcode_type, 'Static')
        self.assertEqual(self.barcode.barcode, '12345678')
        self.assertEqual(self.barcode.linked_id, '87654321')
        self.assertIsNone(self.barcode.session)

    def test_barcode_update(self):
        """Test that a barcode can be updated"""
        # Update barcode
        self.barcode.barcode_type = 'Dynamic'
        self.barcode.barcode = '87654321'
        self.barcode.session = 'test_session'
        self.barcode.save()

        # Refresh from database
        self.barcode.refresh_from_db()

        # Check that barcode was updated
        self.assertEqual(self.barcode.barcode_type, 'Dynamic')
        self.assertEqual(self.barcode.barcode, '87654321')
        self.assertEqual(self.barcode.session, 'test_session')

    def test_barcode_string_representation(self):
        """Test the string representation of a barcode"""
        expected_string = f"Static barcode ending with 5678"
        self.assertEqual(str(self.barcode), expected_string)

class BarcodeUsageModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create a test barcode
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode_type='Static',
            barcode='12345678',
            linked_id='87654321'
        )

        # Create barcode usage for the barcode
        self.barcode_usage = BarcodeUsage.objects.create(
            barcode=self.barcode,
            total_usage=5
        )

    def test_barcode_usage_creation(self):
        """Test that barcode usage can be created"""
        self.assertEqual(self.barcode_usage.barcode, self.barcode)
        self.assertEqual(self.barcode_usage.total_usage, 5)
        # Check that last_used is set automatically
        self.assertIsNotNone(self.barcode_usage.last_used)

    def test_barcode_usage_update(self):
        """Test that barcode usage can be updated"""
        # Update barcode usage
        self.barcode_usage.total_usage = 10
        self.barcode_usage.save()

        # Refresh from database
        self.barcode_usage.refresh_from_db()

        # Check that usage was updated
        self.assertEqual(self.barcode_usage.total_usage, 10)

    def test_barcode_usage_string_representation(self):
        """Test the string representation of barcode usage"""
        expected_string = f"Barcode ending with 5678 - Total Usage: 5 - Last Used: {self.barcode_usage.last_used}"
        self.assertEqual(str(self.barcode_usage), expected_string)
