from unittest.mock import Mock

from django.contrib.auth.models import User, Group
from django.test import TestCase
from index.models import Barcode, BarcodeUsage, UserBarcodeSettings, BarcodeUserProfile


class BarcodeSerializerTest(TestCase):
    """Test BarcodeSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

    def test_serializer_fields(self):
        """Test serializer includes all required fields"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        data = serializer.data

        expected_fields = [
            "id",
            "barcode_type",
            "barcode",
            "time_created",
            "usage_count",
            "last_used",
            "display_name",
            "owner",
            "is_owned_by_current_user",
            "has_profile_addon",
        ]

        for field in expected_fields:
            self.assertIn(field, data)

    def test_usage_count_with_usage_record(self):
        """Test usage_count field with existing usage record"""
        from index.serializers import BarcodeSerializer

        BarcodeUsage.objects.create(barcode=self.barcode, total_usage=10)

        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data["usage_count"], 10)

    def test_usage_count_without_usage_record(self):
        """Test usage_count field without usage record"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data["usage_count"], 0)

    def test_display_name_identification(self):
        """Test display name for identification barcode"""
        from index.serializers import BarcodeSerializer

        self.barcode.barcode_type = "Identification"
        self.barcode.save()

        serializer = BarcodeSerializer(self.barcode)
        expected = "testuser's identification barcode"
        self.assertEqual(serializer.data["display_name"], expected)

    def test_display_name_dynamic(self):
        """Test display name for dynamic barcode"""
        from index.serializers import BarcodeSerializer

        self.barcode.barcode_type = "DynamicBarcode"
        self.barcode.save()

        serializer = BarcodeSerializer(self.barcode)
        expected = "Dynamic Barcode ending with 3456"
        self.assertEqual(serializer.data["display_name"], expected)

    def test_has_profile_addon_true(self):
        """Test has_profile_addon when profile exists"""
        from index.serializers import BarcodeSerializer

        BarcodeUserProfile.objects.create(
            linked_barcode=self.barcode, name="Test User", information_id="TEST123"
        )

        serializer = BarcodeSerializer(self.barcode)
        self.assertTrue(serializer.data["has_profile_addon"])

    def test_has_profile_addon_false(self):
        """Test has_profile_addon when profile doesn't exist"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        self.assertFalse(serializer.data["has_profile_addon"])


class BarcodeCreateSerializerTest(TestCase):
    """Test BarcodeCreateSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.school_group = Group.objects.create(name="School")
        self.user.groups.add(self.school_group)

    def test_validate_barcode_strips_whitespace(self):
        """Test that barcode validation strips whitespace"""
        from index.serializers import BarcodeCreateSerializer

        serializer = BarcodeCreateSerializer()
        result = serializer.validate_barcode("  test123  ")
        self.assertEqual(result, "test123")

    def test_create_dynamic_barcode(self):
        """Test creating dynamic barcode for school user"""
        from index.serializers import BarcodeCreateSerializer

        data = {"barcode": "1234567890123456789012345678"}  # 28 digits
        context = {"request": Mock(user=self.user)}

        serializer = BarcodeCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())

        barcode = serializer.save()
        self.assertEqual(barcode.barcode_type, "DynamicBarcode")
        self.assertEqual(barcode.barcode, "56789012345678")  # Last 14 digits

    def test_create_others_barcode(self):
        """Test creating Others type barcode"""
        from index.serializers import BarcodeCreateSerializer

        data = {"barcode": "regular-barcode-123"}
        context = {"request": Mock(user=self.user)}

        serializer = BarcodeCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())

        barcode = serializer.save()
        self.assertEqual(barcode.barcode_type, "Others")
        self.assertEqual(barcode.barcode, "regular-barcode-123")


class UserBarcodeSettingsSerializerTest(TestCase):
    """Test UserBarcodeSettingsSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.user_group = Group.objects.create(name="User")
        self.school_group = Group.objects.create(name="School")

    def test_field_states_user_group(self):
        """Test field states for User group member"""
        from index.serializers import UserBarcodeSettingsSerializer

        self.user.groups.add(self.user_group)

        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        field_states = serializer.data["field_states"]

        self.assertTrue(field_states["associate_user_profile_disabled"])
        self.assertFalse(field_states["barcode_disabled"])

    def test_field_states_school_group(self):
        """Test field states for School group member"""
        from index.serializers import UserBarcodeSettingsSerializer

        self.user.groups.add(self.school_group)

        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        field_states = serializer.data["field_states"]

        self.assertFalse(field_states["associate_user_profile_disabled"])
        self.assertFalse(field_states["barcode_disabled"])

    def test_validate_user_group_profile_association(self):
        """Test validation prevents User group from enabling profile association"""
        from index.serializers import UserBarcodeSettingsSerializer

        self.user.groups.add(self.user_group)

        data = {"associate_user_profile_with_barcode": True}
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("associate_user_profile_with_barcode", serializer.errors)

    def test_barcode_choices_school_user(self):
        """Test barcode choices for school user"""
        from index.serializers import UserBarcodeSettingsSerializer

        self.user.groups.add(self.school_group)

        # Create barcodes
        dynamic_barcode = Barcode.objects.create(
            user=self.user, barcode="12345678901234", barcode_type="DynamicBarcode"
        )

        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        choices = serializer.data["barcode_choices"]

        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["id"], dynamic_barcode.id)
        self.assertEqual(choices[0]["barcode_type"], "DynamicBarcode")

    def test_barcode_choices_user_type(self):
        """Test barcode choices for User group member (identification only)"""
        from index.serializers import UserBarcodeSettingsSerializer

        self.user.groups.add(self.user_group)

        # Create identification barcode
        ident_barcode = Barcode.objects.create(
            user=self.user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )

        # Create other barcode (should not appear in choices)
        Barcode.objects.create(
            user=self.user, barcode="other123456789", barcode_type="Others"
        )

        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        choices = serializer.data["barcode_choices"]

        # Should only have identification barcode
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["id"], ident_barcode.id)
        self.assertEqual(choices[0]["barcode_type"], "Identification")
