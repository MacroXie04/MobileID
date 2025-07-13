import base64
import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from mobileid.forms.BarcodeForm import BarcodeForm
from mobileid.forms.InfoForm import StudentInformationUpdateForm
from mobileid.models import (Barcode, BarcodeUsage, UserBarcodeSettings,
                             UserProfile)

# test case only for GitHub Action


class BaseTestCase(TestCase):
    """Base test class providing common setup methods"""

    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        # Valid base64 image (1x1 transparent PNG)
        self.valid_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAn8B9p6Q2wAAAABJRU5ErkJggg=="
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

        # Create user profile
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name="Test Student",
            information_id="12345678",
            user_profile_img=self.valid_img,
        )

        # Create test barcode
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode_type="Static",
            barcode="1234567890123456",
            linked_id="87654321",
        )

        # Create barcode settings
        self.barcode_settings = UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=self.barcode,
            server_verification=True,
            timestamp_verification=False,
            barcode_pull=True,
        )

        # Create barcode usage record
        self.barcode_usage = BarcodeUsage.objects.create(
            barcode=self.barcode, total_usage=5
        )


class UserModelTest(BaseTestCase):
    """User model tests"""

    def test_user_creation(self):
        """Test user creation"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpassword123"))
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")

    def test_user_password_validation(self):
        """Test password validation"""
        # Test correct password
        self.assertTrue(self.user.check_password("testpassword123"))

        # Test wrong password
        self.assertFalse(self.user.check_password("wrongpassword"))

    def test_user_string_representation(self):
        """Test user string representation"""
        expected = "testuser"
        self.assertEqual(str(self.user), expected)


class UserProfileModelTest(BaseTestCase):
    """User profile model tests"""

    def test_user_profile_creation(self):
        """Test user profile creation"""
        self.assertEqual(self.user_profile.user, self.user)
        self.assertEqual(self.user_profile.name, "Test Student")
        self.assertEqual(self.user_profile.information_id, "12345678")
        self.assertEqual(self.user_profile.user_profile_img, self.valid_img)

        # Test security field default values
        self.assertEqual(self.user_profile.failed_login_attempts, 0)
        self.assertFalse(self.user_profile.is_locked)
        self.assertIsNone(self.user_profile.locked_until)

    def test_user_profile_string_representation(self):
        """Test user profile string representation"""
        expected = "Test Student - StudentID: **5678"
        self.assertEqual(str(self.user_profile), expected)

    def test_user_profile_update(self):
        """Test user profile update"""
        # Update user profile
        self.user_profile.name = "New Test Student"
        self.user_profile.information_id = "87654321"
        self.user_profile.save()

        # Refresh database
        self.user_profile.refresh_from_db()

        # Verify update
        self.assertEqual(self.user_profile.name, "New Test Student")
        self.assertEqual(self.user_profile.information_id, "87654321")

    def test_user_profile_with_image(self):
        """Test user profile with image"""
        # Create user profile with image
        test_image = base64.b64encode(b"test_image_data").decode("utf-8")
        profile_with_image = UserProfile.objects.create(
            user=User.objects.create_user(username="testuser2", password="testpass"),
            name="User with Image",
            information_id="11111111",
            user_profile_img=test_image,
        )

        self.assertEqual(profile_with_image.user_profile_img, test_image)


class AccountSecurityTest(BaseTestCase):
    """Account security tests"""

    def test_failed_login_attempts_increment(self):
        """Test failed login attempts increment"""
        initial_attempts = self.user_profile.failed_login_attempts

        # Increment failed login attempts
        self.user_profile.failed_login_attempts += 1
        self.user_profile.save()

        # Refresh database
        self.user_profile.refresh_from_db()

        # Verify increment
        self.assertEqual(self.user_profile.failed_login_attempts, initial_attempts + 1)

    def test_account_locking(self):
        """Test account locking"""
        # Set failed login attempts to max value minus 1
        self.user_profile.failed_login_attempts = settings.MAX_FAILED_LOGIN_ATTEMPTS - 1
        self.user_profile.save()

        # Account should not be locked yet
        self.assertFalse(self.user_profile.is_locked)

        # Increment failed login attempts to max value
        self.user_profile.failed_login_attempts += 1

        # Lock account
        self.user_profile.is_locked = True
        self.user_profile.locked_until = timezone.now() + timedelta(
            minutes=settings.ACCOUNT_LOCKOUT_DURATION
        )
        self.user_profile.save()

        # Refresh database
        self.user_profile.refresh_from_db()

        # Account should now be locked
        self.assertTrue(self.user_profile.is_locked)
        self.assertIsNotNone(self.user_profile.locked_until)

    def test_account_unlocking(self):
        """Test account unlocking"""
        # Lock account
        self.user_profile.is_locked = True
        self.user_profile.locked_until = timezone.now() - timedelta(
            minutes=1
        )  # Past time
        self.user_profile.save()

        # Check if lock time has expired
        if self.user_profile.locked_until < timezone.now():
            # Unlock account
            self.user_profile.is_locked = False
            self.user_profile.failed_login_attempts = 0
            self.user_profile.locked_until = None
            self.user_profile.save()

        # Refresh database
        self.user_profile.refresh_from_db()

        # Account should now be unlocked
        self.assertFalse(self.user_profile.is_locked)
        self.assertEqual(self.user_profile.failed_login_attempts, 0)
        self.assertIsNone(self.user_profile.locked_until)

    def test_reset_failed_attempts_on_successful_login(self):
        """Test reset failed attempts on successful login"""
        # Set some failed login attempts
        self.user_profile.failed_login_attempts = 3
        self.user_profile.save()

        # Simulate successful login, reset failed attempts
        self.user_profile.failed_login_attempts = 0
        self.user_profile.save()

        # Refresh database
        self.user_profile.refresh_from_db()

        # Verify failed attempts have been reset
        self.assertEqual(self.user_profile.failed_login_attempts, 0)


class BarcodeModelTest(BaseTestCase):
    """Barcode model tests"""

    def test_barcode_creation(self):
        """Test barcode creation"""
        self.assertEqual(self.barcode.user, self.user)
        self.assertEqual(self.barcode.barcode_type, "Static")
        self.assertEqual(self.barcode.barcode, "1234567890123456")
        self.assertEqual(self.barcode.linked_id, "87654321")
        self.assertIsNone(self.barcode.session)

    def test_barcode_update(self):
        """Test barcode update"""
        # Update barcode
        self.barcode.barcode_type = "Dynamic"
        self.barcode.barcode = "8765432109876543"
        self.barcode.session = "test_session_123"
        self.barcode.save()

        # Refresh database
        self.barcode.refresh_from_db()

        # Verify update
        self.assertEqual(self.barcode.barcode_type, "Dynamic")
        self.assertEqual(self.barcode.barcode, "8765432109876543")
        self.assertEqual(self.barcode.session, "test_session_123")

    def test_barcode_string_representation(self):
        """Test barcode string representation"""
        expected = "Static barcode ending with 3456"
        self.assertEqual(str(self.barcode), expected)

    def test_barcode_choices(self):
        """Test barcode type choices"""
        # Test all barcode types
        barcode_types = ["Dynamic", "Static", "Others"]

        for barcode_type in barcode_types:
            barcode = Barcode.objects.create(
                user=self.user,
                barcode_type=barcode_type,
                barcode=f"test_{barcode_type.lower()}",
                linked_id="test_id",
            )
            self.assertEqual(barcode.barcode_type, barcode_type)

    def test_barcode_without_linked_id(self):
        """Test barcode without linked ID"""
        barcode_no_linked = Barcode.objects.create(
            user=self.user,
            barcode_type="Dynamic",
            barcode="test_barcode_no_linked",
            linked_id=None,
        )

        self.assertIsNone(barcode_no_linked.linked_id)

    def test_barcode_with_session(self):
        """Test barcode with session"""
        barcode_with_session = Barcode.objects.create(
            user=self.user,
            barcode_type="Dynamic",
            barcode="test_barcode_with_session",
            linked_id="test_id",
            session="test_session_data",
        )

        self.assertEqual(barcode_with_session.session, "test_session_data")


class BarcodeUsageModelTest(BaseTestCase):
    """Barcode usage model tests"""

    def test_barcode_usage_creation(self):
        """Test barcode usage creation"""
        self.assertEqual(self.barcode_usage.barcode, self.barcode)
        self.assertEqual(self.barcode_usage.total_usage, 5)
        self.assertIsNotNone(self.barcode_usage.last_used)

    def test_barcode_usage_update(self):
        """Test barcode usage update"""
        # Update usage count
        self.barcode_usage.total_usage = 15
        self.barcode_usage.save()

        # Refresh database
        self.barcode_usage.refresh_from_db()

        # Verify update
        self.assertEqual(self.barcode_usage.total_usage, 15)

    def test_barcode_usage_string_representation(self):
        """Test barcode usage string representation"""
        expected_start = "Barcode ending with 3456 - Total Usage: 5 - Last Used:"
        self.assertTrue(str(self.barcode_usage).startswith(expected_start))

    def test_barcode_usage_increment(self):
        """Test barcode usage increment"""
        initial_usage = self.barcode_usage.total_usage

        # Increment usage count
        self.barcode_usage.total_usage += 1
        self.barcode_usage.save()

        # Refresh database
        self.barcode_usage.refresh_from_db()

        # Verify increment
        self.assertEqual(self.barcode_usage.total_usage, initial_usage + 1)

    def test_barcode_usage_last_used_auto_update(self):
        """Test barcode usage auto-update time"""
        original_last_used = self.barcode_usage.last_used

        # Wait a short time
        import time

        time.sleep(0.1)

        # Save record (will trigger auto_now)
        self.barcode_usage.save()

        # Refresh database
        self.barcode_usage.refresh_from_db()

        # Verify time has been updated
        self.assertGreater(self.barcode_usage.last_used, original_last_used)


class UserBarcodeSettingsTest(BaseTestCase):
    """User barcode settings tests"""

    def test_barcode_settings_creation(self):
        """Test barcode settings creation"""
        self.assertEqual(self.barcode_settings.user, self.user)
        self.assertEqual(self.barcode_settings.barcode, self.barcode)
        self.assertTrue(self.barcode_settings.server_verification)
        self.assertFalse(self.barcode_settings.timestamp_verification)
        self.assertTrue(self.barcode_settings.barcode_pull)

    def test_barcode_settings_update(self):
        """Test barcode settings update"""
        # Update settings
        self.barcode_settings.server_verification = False
        self.barcode_settings.timestamp_verification = True
        self.barcode_settings.barcode_pull = False
        self.barcode_settings.save()

        # Refresh database
        self.barcode_settings.refresh_from_db()

        # Verify update
        self.assertFalse(self.barcode_settings.server_verification)
        self.assertTrue(self.barcode_settings.timestamp_verification)
        self.assertFalse(self.barcode_settings.barcode_pull)

    def test_barcode_settings_with_null_barcode(self):
        """Test settings with null barcode"""
        # Update settings to null barcode
        self.barcode_settings.barcode = None
        self.barcode_settings.save()

        # Refresh database
        self.barcode_settings.refresh_from_db()

        # Verify settings
        self.assertEqual(self.barcode_settings.user, self.user)
        self.assertIsNone(self.barcode_settings.barcode)

    def test_barcode_settings_string_representation(self):
        """Test barcode settings string representation"""
        expected = "testuser's Barcode Settings"
        self.assertEqual(str(self.barcode_settings), expected)

    def test_barcode_settings_default_values(self):
        """Test barcode settings default values"""
        # Create barcode settings for new user
        new_user = User.objects.create_user(username="newuser", password="testpass")
        new_settings = UserBarcodeSettings.objects.create(user=new_user)

        # Verify default values
        self.assertFalse(new_settings.server_verification)
        self.assertTrue(new_settings.timestamp_verification)
        self.assertTrue(new_settings.barcode_pull)
        self.assertIsNone(new_settings.barcode)


class FormTest(BaseTestCase):
    """Form tests"""

    def test_barcode_form_valid(self):
        """Test barcode form validation"""
        form_data = {"source_type": "barcode", "input_value": "1234567890123456"}
        form = BarcodeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_barcode_form_invalid(self):
        """Test barcode form invalid data"""
        # Missing required field
        form_data = {"source_type": "barcode"}
        form = BarcodeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_barcode_form_invalid_digits(self):
        """Test barcode form non-numeric input"""
        form_data = {"source_type": "barcode", "input_value": "abc123"}
        form = BarcodeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_info_form_valid(self):
        """Test info form validation"""
        form_data = {"name": "Test User", "information_id": "12345678"}
        form = StudentInformationUpdateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_info_form_invalid(self):
        """Test info form invalid data"""
        # Missing required field
        form_data = {"name": "Test User"}
        form = StudentInformationUpdateForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewTest(BaseTestCase):
    """View tests"""

    def test_index_view_authenticated(self):
        """Test authenticated user index view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("mobileid:web_index"))
        self.assertEqual(response.status_code, 200)

    def test_index_view_unauthenticated(self):
        """Test unauthenticated user index view"""
        response = self.client.get(reverse("mobileid:web_index"))
        self.assertEqual(response.status_code, 302)  # Redirect to login page

    def test_manage_barcode_view_authenticated(self):
        """Test authenticated user barcode management view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("mobileid:web_manage_barcode"))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_view_authenticated(self):
        """Test authenticated user profile edit view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("mobileid:web_edit_profile"))
        self.assertEqual(response.status_code, 200)

    def test_settings_edit_view_authenticated(self):
        """Test authenticated user settings edit view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("mobileid:web_barcode_settings"))
        self.assertEqual(response.status_code, 200)


class APITest(APITestCase):
    """API tests"""

    def setUp(self):
        """Set up API test environment"""
        self.client = APIClient()
        self.valid_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAn8B9p6Q2wAAAABJRU5ErkJggg=="
        # Create test user
        self.user = User.objects.create_user(
            username="apiuser", password="testpassword123", email="api@example.com"
        )
        # Create user profile
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name="API Test User",
            information_id="87654321",
            user_profile_img=self.valid_img,
        )

        # Create barcode settings
        self.barcode_settings = UserBarcodeSettings.objects.create(
            user=self.user,
            barcode_pull=True,
            server_verification=False,
            timestamp_verification=True,
        )

        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_get_user_profile_api(self):
        """Test get user profile API"""
        response = self.client.get("/api/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["userprofile"]["name"], "API Test User")
        self.assertEqual(response.data["userprofile"]["information_id"], "87654321")

    def test_update_user_profile_api(self):
        """Test update user profile API"""
        update_data = {
            "userprofile": {
                "name": "Updated API User",
                "information_id": "11111111",
                "user_profile_img": self.user_profile.user_profile_img,
            }
        }
        response = self.client.put("/api/me/", update_data, format="json")
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            if hasattr(response, "data"):
                print(f"Response data: {response.data}")
            else:
                print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["userprofile"]["name"], "Updated API User")

    def test_generate_barcode_api(self):
        """Test generate barcode API"""
        # Create test barcode
        barcode = Barcode.objects.create(
            user=self.user,
            barcode_type="Static",
            barcode="9876543210987654",
            linked_id="12345678",
        )

        # Update barcode settings to use this barcode
        self.barcode_settings.barcode = barcode
        self.barcode_settings.barcode_pull = False
        self.barcode_settings.save()

        response = self.client.post("/api/generate_barcode/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["barcode_type"], "static")

    def test_get_user_barcodes_api(self):
        """Test get user barcodes API"""
        # Create test barcode
        Barcode.objects.create(
            user=self.user,
            barcode_type="Static",
            barcode="1234567890123456",
            linked_id="87654321",
        )

        response = self.client.get("/api/barcodes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_barcode_api(self):
        """Test delete barcode API"""
        # Create test barcode
        barcode = Barcode.objects.create(
            user=self.user,
            barcode_type="Static",
            barcode="1234567890123456",
            linked_id="87654321",
        )

        response = self.client.delete(f"/api/barcodes/{barcode.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify barcode has been deleted
        self.assertFalse(Barcode.objects.filter(id=barcode.id).exists())

    def test_api_authentication_required(self):
        """Test API requires authentication"""
        # Clear authentication
        self.client.credentials()

        response = self.client.get("/api/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class IntegrationTest(BaseTestCase):
    """Integration tests"""

    def test_complete_user_workflow(self):
        """Test complete user workflow"""
        # 1. User login
        self.client.force_login(self.user)

        # 2. Visit index page
        response = self.client.get(reverse("mobileid:web_index"))
        self.assertEqual(response.status_code, 200)

        # 3. Visit barcode management page
        response = self.client.get(reverse("mobileid:web_manage_barcode"))
        self.assertEqual(response.status_code, 200)

        # 4. Visit profile edit page
        response = self.client.get(reverse("mobileid:web_edit_profile"))
        self.assertEqual(response.status_code, 200)

        # 5. Visit settings edit page
        response = self.client.get(reverse("mobileid:web_barcode_settings"))
        self.assertEqual(response.status_code, 200)

    def test_barcode_workflow(self):
        """Test barcode workflow"""
        # 1. Create barcode
        barcode = Barcode.objects.create(
            user=self.user,
            barcode_type="Dynamic",
            barcode="dynamic_barcode_123",
            linked_id="dynamic_id_456",
        )

        # 2. Create barcode usage record
        usage = BarcodeUsage.objects.create(barcode=barcode, total_usage=1)

        # 3. Update barcode settings
        self.barcode_settings.barcode = barcode
        self.barcode_settings.save()

        # 4. Verify relationships
        self.assertEqual(self.barcode_settings.barcode, barcode)
        self.assertEqual(usage.barcode, barcode)
        self.assertEqual(barcode.user, self.user)

    def test_user_profile_workflow(self):
        """Test user profile workflow"""
        # 1. Update user profile
        self.user_profile.name = "Workflow Test User"
        self.user_profile.information_id = "99999999"
        self.user_profile.save()

        # 2. Verify update
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.name, "Workflow Test User")
        self.assertEqual(self.user_profile.information_id, "99999999")

        # 3. Test string representation
        expected = "Workflow Test User - StudentID: **9999"
        self.assertEqual(str(self.user_profile), expected)


class PerformanceTest(BaseTestCase):
    """Performance tests"""

    def test_bulk_barcode_creation(self):
        """Test bulk barcode creation performance"""
        import time

        start_time = time.time()

        # Create 100 barcodes
        barcodes = []
        for i in range(100):
            barcode = Barcode(
                user=self.user,
                barcode_type="Static",
                barcode=f"barcode_{i:03d}",
                linked_id=f"id_{i:03d}",
            )
            barcodes.append(barcode)

        # Bulk create
        Barcode.objects.bulk_create(barcodes)

        end_time = time.time()
        creation_time = end_time - start_time

        # Verify creation success
        self.assertEqual(Barcode.objects.count(), 101)  # Including 1 created in setUp

        # Performance check (creating 100 barcodes should complete in reasonable time)
        self.assertLess(creation_time, 1.0)  # Complete within 1 second

    def test_bulk_usage_creation(self):
        """Test bulk usage record creation performance"""
        import time

        # Create multiple barcodes
        barcodes = []
        for i in range(50):
            barcode = Barcode.objects.create(
                user=self.user,
                barcode_type="Static",
                barcode=f"perf_barcode_{i:03d}",
                linked_id=f"perf_id_{i:03d}",
            )
            barcodes.append(barcode)

        start_time = time.time()

        # Create usage records
        usages = []
        for barcode in barcodes:
            usage = BarcodeUsage(barcode=barcode, total_usage=1)
            usages.append(usage)

        BarcodeUsage.objects.bulk_create(usages)

        end_time = time.time()
        creation_time = end_time - start_time

        # Verify creation success
        self.assertEqual(
            BarcodeUsage.objects.count(), 51
        )  # Including 1 created in setUp

        # Performance check
        self.assertLess(creation_time, 0.5)  # Complete within 0.5 seconds


class SecurityTest(BaseTestCase):
    """Security tests"""

    def test_user_profile_data_isolation(self):
        """Test user profile data isolation"""
        # Create another user
        other_user = User.objects.create_user(username="otheruser", password="testpass")

        other_profile = UserProfile.objects.create(
            user=other_user,
            name="Other User",
            information_id="55555555",
            user_profile_img="",
        )

        # Verify data isolation
        self.assertNotEqual(self.user_profile.user, other_profile.user)
        self.assertNotEqual(
            self.user_profile.information_id, other_profile.information_id
        )

    def test_barcode_user_isolation(self):
        """Test barcode user isolation"""
        # Create another user
        other_user = User.objects.create_user(username="otheruser", password="testpass")

        other_barcode = Barcode.objects.create(
            user=other_user,
            barcode_type="Static",
            barcode="other_barcode",
            linked_id="other_id",
        )

        # Verify data isolation
        self.assertNotEqual(self.barcode.user, other_barcode.user)
        self.assertNotEqual(self.barcode.barcode, other_barcode.barcode)

    def test_sensitive_data_not_exposed(self):
        """Test sensitive data not exposed"""
        # Test user profile string representation doesn't expose full ID
        profile_str = str(self.user_profile)
        self.assertNotIn(self.user_profile.information_id, profile_str)
        self.assertIn("**5678", profile_str)  # Only show last 4 digits

        # Test barcode string representation doesn't expose full barcode
        barcode_str = str(self.barcode)
        self.assertNotIn(self.barcode.barcode, barcode_str)
        self.assertIn("3456", barcode_str)  # Only show last 4 digits


class EdgeCaseTest(BaseTestCase):
    """Edge case tests"""

    def test_empty_string_fields(self):
        """Test empty string fields"""
        # Test barcode with empty strings
        empty_barcode = Barcode.objects.create(
            user=self.user, barcode_type="Static", barcode="", linked_id=""
        )

        self.assertEqual(empty_barcode.barcode, "")
        self.assertEqual(empty_barcode.linked_id, "")

    def test_very_long_fields(self):
        """Test very long fields"""
        long_string = "a" * 1000

        # Test very long barcode
        long_barcode = Barcode.objects.create(
            user=self.user,
            barcode_type="Static",
            barcode=long_string,
            linked_id="test_id",
        )

        self.assertEqual(long_barcode.barcode, long_string)

    def test_special_characters(self):
        """Test special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Test special characters in barcode
        special_barcode = Barcode.objects.create(
            user=self.user,
            barcode_type="Static",
            barcode=special_chars,
            linked_id="test_id",
        )

        self.assertEqual(special_barcode.barcode, special_chars)

    def test_unicode_characters(self):
        """Test Unicode characters"""
        unicode_string = "Test Barcode 🎯📱💻"

        # Test Unicode characters in user profile
        self.user_profile.name = unicode_string
        self.user_profile.save()

        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.name, unicode_string)


class HealthCheckTest(TestCase):
    """Health check endpoint tests"""

    def test_health_check_endpoint(self):
        """Test health check endpoint returns healthy status"""
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("checks", data)
        self.assertEqual(data["checks"]["database"], "healthy")
        self.assertEqual(data["checks"]["application"], "healthy")

    def test_health_check_method_not_allowed(self):
        """Test health check endpoint only allows GET requests"""
        response = self.client.post("/health/")
        self.assertEqual(response.status_code, 405)

        response = self.client.put("/health/")
        self.assertEqual(response.status_code, 405)

        response = self.client.delete("/health/")
        self.assertEqual(response.status_code, 405)

    def test_health_check_response_structure(self):
        """Test health check response has correct structure"""
        response = self.client.get("/health/")
        data = json.loads(response.content)

        # Check required fields
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("database", data["checks"])
        self.assertIn("cache", data["checks"])
        self.assertIn("application", data["checks"])

        # Check status values
        self.assertIn(data["status"], ["healthy", "unhealthy"])
        self.assertIn(data["checks"]["database"], ["healthy", "unhealthy"])
        self.assertIn(data["checks"]["cache"], ["healthy", "unhealthy"])
        self.assertIn(data["checks"]["application"], ["healthy", "unhealthy"])
