from django.contrib.auth.models import User
from django.test import TestCase
from index.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
    BarcodeUserProfile,
)


class BarcodeModelTest(TestCase):
    """Test Barcode model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_barcode_creation(self):
        """Test creating a Barcode"""
        barcode = Barcode.objects.create(
            user=self.user,
            barcode="12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678",  # noqa: E501
            barcode_type="DynamicBarcode",
        )

        self.assertEqual(barcode.user, self.user)
        self.assertEqual(barcode.barcode_type, "DynamicBarcode")
        self.assertIsNotNone(barcode.barcode_uuid)
        self.assertIsNotNone(barcode.time_created)

    def test_barcode_str_representation(self):
        """Test Barcode __str__ method for different types"""
        # Dynamic barcode
        dynamic_barcode = Barcode.objects.create(
            user=self.user,
            barcode="1234567890123456",
            barcode_type="DynamicBarcode",
        )
        self.assertEqual(
            str(dynamic_barcode), "Dynamic barcode ending with 3456"
        )

        # Identification barcode - use different barcode value
        ident_barcode = Barcode.objects.create(
            user=self.user,
            barcode="9876543210987654",
            barcode_type="Identification",
        )
        self.assertEqual(
            str(ident_barcode), "testuser's identification Barcode"
        )

        # Others barcode - use different barcode value
        other_barcode = Barcode.objects.create(
            user=self.user, barcode="5678901234567890", barcode_type="Others"
        )
        self.assertEqual(str(other_barcode), "Barcode ending with 7890")

    def test_barcode_type_choices(self):
        """Test barcode type choices"""
        choices = dict(Barcode.BARCODE_TYPE_CHOICES)
        self.assertIn("DynamicBarcode", choices)
        self.assertIn("Identification", choices)
        self.assertIn("Others", choices)

    def test_barcode_unique_constraint(self):
        """Test that barcode values must be unique"""
        _ = Barcode.objects.create(
            user=self.user, barcode="uniquebarcode123", barcode_type="Others"
        )

        # Creating another barcode with the same value should raise error
        user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )
        with self.assertRaises(Exception):  # noqa: B017
            Barcode.objects.create(
                user=user2, barcode="uniquebarcode123", barcode_type="Others"
            )


class BarcodeUsageModelTest(TestCase):
    """Test BarcodeUsage model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

    def test_barcode_usage_creation(self):
        """Test creating BarcodeUsage"""
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode, total_usage=5
        )

        self.assertEqual(usage.barcode, self.barcode)
        self.assertEqual(usage.total_usage, 5)
        self.assertIsNotNone(usage.last_used)

    def test_barcode_usage_str_representation(self):
        """Test BarcodeUsage __str__ method"""
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode, total_usage=10
        )

        expected = f"Barcode ending with 3456 - Total Usage: 10 - Last Used: {usage.last_used}"  # noqa: E501
        self.assertEqual(str(usage), expected)

    def test_barcode_usage_auto_now(self):
        """Test that last_used is automatically updated"""
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode, total_usage=1
        )
        original_time = usage.last_used

        # Update usage
        usage.total_usage = 2
        usage.save()

        # last_used should be updated
        usage.refresh_from_db()
        self.assertNotEqual(usage.last_used, original_time)


class UserBarcodeSettingsModelTest(TestCase):
    """Test UserBarcodeSettings model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

    def test_user_barcode_settings_creation(self):
        """Test creating UserBarcodeSettings"""
        settings = UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=self.barcode,
            server_verification=True,
            associate_user_profile_with_barcode=True,
        )

        self.assertEqual(settings.user, self.user)
        self.assertEqual(settings.barcode, self.barcode)
        self.assertTrue(settings.server_verification)
        self.assertTrue(settings.associate_user_profile_with_barcode)

    def test_user_barcode_settings_str_representation(self):
        """Test UserBarcodeSettings __str__ method"""
        settings = UserBarcodeSettings.objects.create(
            user=self.user, barcode=self.barcode
        )

        expected = "testuser's Barcode Settings"
        self.assertEqual(str(settings), expected)

    def test_user_barcode_settings_defaults(self):
        """Test default values for UserBarcodeSettings"""
        settings = UserBarcodeSettings.objects.create(user=self.user)

        self.assertFalse(settings.server_verification)
        self.assertFalse(settings.associate_user_profile_with_barcode)
        self.assertIsNone(settings.barcode)


class BarcodeUserProfileModelTest(TestCase):
    """Test BarcodeUserProfile model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

    def test_barcode_user_profile_creation(self):
        """Test creating BarcodeUserProfile"""
        profile = BarcodeUserProfile.objects.create(
            linked_barcode=self.barcode,
            name="Test User",
            information_id="TEST123",
            user_profile_img="base64encodedimage",
        )

        self.assertEqual(profile.linked_barcode, self.barcode)
        self.assertEqual(profile.name, "Test User")
        self.assertEqual(profile.information_id, "TEST123")
        self.assertEqual(profile.user_profile_img, "base64encodedimage")
