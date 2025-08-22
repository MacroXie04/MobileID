import json
from unittest.mock import patch, Mock

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from authn.models import UserProfile
from authn.services.webauthn import create_user_profile
from index.models import Barcode, BarcodeUsage, UserBarcodeSettings, BarcodeUserProfile
from index.services.barcode import (
    generate_barcode,
    generate_unique_identification_barcode,
    _create_identification_barcode,
    _touch_barcode_usage,
    _random_digits
)


class BarcodeModelTest(TestCase):
    """Test Barcode model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_barcode_creation(self):
        """Test creating a Barcode"""
        barcode = Barcode.objects.create(
            user=self.user,
            barcode='12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678',
            barcode_type='DynamicBarcode'
        )
        
        self.assertEqual(barcode.user, self.user)
        self.assertEqual(barcode.barcode_type, 'DynamicBarcode')
        self.assertIsNotNone(barcode.barcode_uuid)
        self.assertIsNotNone(barcode.time_created)

    def test_barcode_str_representation(self):
        """Test Barcode __str__ method for different types"""
        # Dynamic barcode
        dynamic_barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='DynamicBarcode'
        )
        self.assertEqual(str(dynamic_barcode), 'Dynamic barcode ending with 3456')
        
        # Identification barcode - use different barcode value
        ident_barcode = Barcode.objects.create(
            user=self.user,
            barcode='9876543210987654',
            barcode_type='Identification'
        )
        self.assertEqual(str(ident_barcode), 'testuser\'s identification Barcode')
        
        # Others barcode - use different barcode value
        other_barcode = Barcode.objects.create(
            user=self.user,
            barcode='5678901234567890',
            barcode_type='Others'
        )
        self.assertEqual(str(other_barcode), 'Barcode ending with 7890')

    def test_barcode_type_choices(self):
        """Test barcode type choices"""
        choices = dict(Barcode.BARCODE_TYPE_CHOICES)
        self.assertIn('DynamicBarcode', choices)
        self.assertIn('Identification', choices)
        self.assertIn('Others', choices)

    def test_barcode_unique_constraint(self):
        """Test that barcode values must be unique"""
        barcode1 = Barcode.objects.create(
            user=self.user,
            barcode='uniquebarcode123',
            barcode_type='Others'
        )
        
        # Creating another barcode with the same value should raise error
        user2 = User.objects.create_user(username='testuser2', password='testpass123')
        with self.assertRaises(Exception):
            Barcode.objects.create(
                user=user2,
                barcode='uniquebarcode123',
                barcode_type='Others'
            )


class BarcodeUsageModelTest(TestCase):
    """Test BarcodeUsage model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='Others'
        )

    def test_barcode_usage_creation(self):
        """Test creating BarcodeUsage"""
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode,
            total_usage=5
        )
        
        self.assertEqual(usage.barcode, self.barcode)
        self.assertEqual(usage.total_usage, 5)
        self.assertIsNotNone(usage.last_used)

    def test_barcode_usage_str_representation(self):
        """Test BarcodeUsage __str__ method"""
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode,
            total_usage=10
        )
        
        expected = f'Barcode ending with 3456 - Total Usage: 10 - Last Used: {usage.last_used}'
        self.assertEqual(str(usage), expected)

    def test_barcode_usage_auto_now(self):
        """Test that last_used is automatically updated"""
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode,
            total_usage=1
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
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='Others'
        )

    def test_user_barcode_settings_creation(self):
        """Test creating UserBarcodeSettings"""
        settings = UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=self.barcode,
            server_verification=True,
            associate_user_profile_with_barcode=True
        )
        
        self.assertEqual(settings.user, self.user)
        self.assertEqual(settings.barcode, self.barcode)
        self.assertTrue(settings.server_verification)
        self.assertTrue(settings.associate_user_profile_with_barcode)

    def test_user_barcode_settings_str_representation(self):
        """Test UserBarcodeSettings __str__ method"""
        settings = UserBarcodeSettings.objects.create(
            user=self.user,
            barcode=self.barcode
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
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='Others'
        )

    def test_barcode_user_profile_creation(self):
        """Test creating BarcodeUserProfile"""
        profile = BarcodeUserProfile.objects.create(
            linked_barcode=self.barcode,
            name='Test User',
            information_id='TEST123',
            user_profile_img='base64encodedimage'
        )
        
        self.assertEqual(profile.linked_barcode, self.barcode)
        self.assertEqual(profile.name, 'Test User')
        self.assertEqual(profile.information_id, 'TEST123')
        self.assertEqual(profile.user_profile_img, 'base64encodedimage')


class BarcodeServiceTest(TestCase):
    """Test barcode service functions"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.school_user = User.objects.create_user(username='schooluser', password='testpass123')
        self.staff_user = User.objects.create_user(username='staffuser', password='testpass123')
        
        # Create groups
        self.user_group = Group.objects.create(name='User')
        self.school_group = Group.objects.create(name='School')
        self.staff_group = Group.objects.create(name='Staff')
        
        # Assign users to groups
        self.user.groups.add(self.user_group)
        self.school_user.groups.add(self.school_group)
        self.staff_user.groups.add(self.staff_group)

    def test_random_digits(self):
        """Test _random_digits helper function"""
        digits = _random_digits(10)
        self.assertEqual(len(digits), 10)
        self.assertTrue(digits.isdigit())

    def test_generate_unique_identification_barcode(self):
        """Test generating unique identification barcode"""
        barcode1 = generate_unique_identification_barcode()
        barcode2 = generate_unique_identification_barcode()
        
        self.assertEqual(len(barcode1), 28)
        self.assertEqual(len(barcode2), 28)
        self.assertTrue(barcode1.isdigit())
        self.assertTrue(barcode2.isdigit())
        self.assertNotEqual(barcode1, barcode2)

    @patch('index.services.barcode.Barcode.objects.filter')
    def test_generate_unique_identification_barcode_max_attempts(self, mock_filter):
        """Test max attempts for unique barcode generation"""
        # Mock that all generated barcodes already exist
        mock_filter.return_value.exists.return_value = True
        
        with self.assertRaises(RuntimeError):
            generate_unique_identification_barcode(50)  # Pass max_attempts parameter

    def test_create_identification_barcode(self):
        """Test creating identification barcode"""
        # Create an existing identification barcode
        existing_barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456789012345678',
            barcode_type='Identification'
        )
        
        # Create new identification barcode
        new_barcode = _create_identification_barcode(self.user)
        
        # Check that old barcode was deleted
        self.assertFalse(Barcode.objects.filter(id=existing_barcode.id).exists())
        
        # Check new barcode
        self.assertEqual(new_barcode.user, self.user)
        self.assertEqual(new_barcode.barcode_type, 'Identification')
        self.assertEqual(len(new_barcode.barcode), 28)

    def test_touch_barcode_usage_new_barcode(self):
        """Test updating usage for barcode without existing usage record"""
        barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='Others'
        )
        
        _touch_barcode_usage(barcode)
        
        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)

    def test_touch_barcode_usage_existing_barcode(self):
        """Test updating usage for barcode with existing usage record"""
        barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='Others'
        )
        
        # Create initial usage
        BarcodeUsage.objects.create(barcode=barcode, total_usage=5)
        
        _touch_barcode_usage(barcode)
        
        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 6)

    def test_generate_barcode_staff_user(self):
        """Test barcode generation for staff user (should fail)"""
        result = generate_barcode(self.staff_user)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Staff accounts cannot generate barcodes.')

    def test_generate_barcode_invalid_group(self):
        """Test barcode generation for user with no valid group"""
        user_no_group = User.objects.create_user(username='nogroup', password='test123')
        
        result = generate_barcode(user_no_group)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Invalid user group.')

    def test_generate_barcode_user_group_new(self):
        """Test barcode generation for User group member without existing barcode"""
        result = generate_barcode(self.user)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['barcode_type'], 'Identification')
        self.assertEqual(len(result['barcode']), 28)
        
        # Check that identification barcode was created
        barcode = Barcode.objects.get(user=self.user, barcode_type='Identification')
        self.assertEqual(barcode.barcode, result['barcode'])

    def test_generate_barcode_user_group_existing(self):
        """Test barcode generation for User group member with existing barcode"""
        # Create existing identification barcode
        existing_barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456789012345678',
            barcode_type='Identification'
        )
        
        result = generate_barcode(self.user)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['barcode_type'], 'Identification')
        
        # Check that new barcode was created and old one was deleted
        self.assertFalse(Barcode.objects.filter(id=existing_barcode.id).exists())
        new_barcode = Barcode.objects.get(user=self.user, barcode_type='Identification')
        self.assertNotEqual(new_barcode.barcode, existing_barcode.barcode)

    def test_generate_barcode_school_group_no_selection(self):
        """Test barcode generation for School group member with no barcode selected"""
        result = generate_barcode(self.school_user)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'No barcode selected.')

    def test_generate_barcode_school_group_dynamic(self):
        """Test barcode generation for School group member with dynamic barcode"""
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='12345678901234',
            barcode_type='DynamicBarcode'
        )
        
        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=dynamic_barcode
        )
        
        with patch('index.services.barcode._timestamp', return_value='20231201120000'):
            result = generate_barcode(self.school_user)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['barcode_type'], 'DynamicBarcode')
        self.assertEqual(result['barcode'], '2023120112000012345678901234')
        self.assertIn('Dynamic: 1234', result['message'])

    def test_generate_barcode_school_group_others(self):
        """Test barcode generation for School group member with Others barcode"""
        other_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='static123456789',
            barcode_type='Others'
        )
        
        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=other_barcode
        )
        
        result = generate_barcode(self.school_user)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['barcode_type'], 'Others')
        self.assertEqual(result['barcode'], 'static123456789')
        self.assertIn('Barcode ending with 6789', result['message'])

    def test_generate_barcode_dynamic_with_server_verification_disabled(self):
        """Test dynamic barcode generation with server verification disabled"""
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='12345678901234',
            barcode_type='DynamicBarcode'
        )
        
        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=dynamic_barcode,
            server_verification=False  # Disabled to avoid session attribute error
        )
        
        with patch('index.services.barcode._timestamp', return_value='20231201120000'):
            result = generate_barcode(self.school_user)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('Dynamic: 1234', result['message'])


class GenerateBarcodeAPITest(APITestCase):
    """Test GenerateBarcodeAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.user_group = Group.objects.create(name='User')
        self.user.groups.add(self.user_group)
        
        create_user_profile(self.user, 'Test User', 'TEST123', None)
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_generate_barcode_success(self):
        """Test successful barcode generation"""
        url = reverse('index:api_generate_barcode')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['barcode_type'], 'Identification')

    def test_generate_barcode_unauthenticated(self):
        """Test barcode generation without authentication"""
        self.client.credentials()  # Remove authentication
        
        url = reverse('index:api_generate_barcode')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BarcodeDashboardAPITest(APITestCase):
    """Test BarcodeDashboardAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.school_user = User.objects.create_user(username='schooluser', password='testpass123')
        self.user_user = User.objects.create_user(username='regularuser', password='testpass123')
        
        # Create groups
        self.school_group = Group.objects.create(name='School')
        self.user_group = Group.objects.create(name='User')
        
        # Assign users to groups - School users should NOT be in User group
        self.school_user.groups.add(self.school_group)
        self.user_user.groups.add(self.user_group)
        
        # Don't use create_user_profile as it adds users to User group automatically
        # Create profiles manually for School user
        UserProfile.objects.create(
            user=self.school_user,
            name='School User',
            information_id='SCHOOL123'
        )
        
        create_user_profile(self.user_user, 'Regular User', 'USER123', None)

    def _authenticate_user(self, user):
        """Helper to authenticate a user"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_dashboard_get_school_user(self):
        """Test getting dashboard data for school user"""
        self._authenticate_user(self.school_user)
        
        # Create some barcodes
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='12345678901234',
            barcode_type='DynamicBarcode'
        )
        other_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='static123456789',
            barcode_type='Others'
        )
        
        url = reverse('index:api_barcode_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('settings', response.data)
        self.assertIn('barcodes', response.data)
        self.assertTrue(response.data['is_school_group'])
        self.assertFalse(response.data['is_user_group'])
        
        # Should have 2 barcodes
        self.assertEqual(len(response.data['barcodes']), 2)

    def test_dashboard_get_regular_user_forbidden(self):
        """Test that regular users cannot access dashboard"""
        self._authenticate_user(self.user_user)
        
        url = reverse('index:api_barcode_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('User type accounts cannot access', response.data['detail'])

    def test_dashboard_post_update_settings(self):
        """Test updating barcode settings"""
        self._authenticate_user(self.school_user)
        
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='12345678901234',
            barcode_type='DynamicBarcode'
        )
        
        url = reverse('index:api_barcode_dashboard')
        data = {
            'barcode': barcode.id,
            'server_verification': True,
            'associate_user_profile_with_barcode': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Check settings were updated
        settings = UserBarcodeSettings.objects.get(user=self.school_user)
        self.assertEqual(settings.barcode, barcode)
        self.assertTrue(settings.server_verification)

    def test_dashboard_put_create_barcode(self):
        """Test creating new barcode"""
        self._authenticate_user(self.school_user)
        
        url = reverse('index:api_barcode_dashboard')
        data = {'barcode': 'newbarcode123456789'}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        
        # Check barcode was created
        barcode = Barcode.objects.get(barcode='newbarcode123456789')
        self.assertEqual(barcode.user, self.school_user)
        self.assertEqual(barcode.barcode_type, 'Others')

    def test_dashboard_put_create_dynamic_barcode(self):
        """Test creating dynamic barcode (28 digits)"""
        self._authenticate_user(self.school_user)
        
        url = reverse('index:api_barcode_dashboard')
        data = {'barcode': '1234567890123456789012345678'}  # 28 digits
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check barcode was created as dynamic with last 14 digits
        barcode = Barcode.objects.get(user=self.school_user, barcode_type='DynamicBarcode')
        self.assertEqual(barcode.barcode, '56789012345678')  # Last 14 digits

    def test_dashboard_delete_barcode(self):
        """Test deleting barcode"""
        self._authenticate_user(self.school_user)
        
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='deleteme123456789',
            barcode_type='Others'
        )
        
        url = reverse('index:api_barcode_dashboard')
        data = {'barcode_id': barcode.id}
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Check barcode was deleted
        self.assertFalse(Barcode.objects.filter(id=barcode.id).exists())

    def test_dashboard_delete_barcode_not_found(self):
        """Test deleting non-existent barcode"""
        self._authenticate_user(self.school_user)
        
        url = reverse('index:api_barcode_dashboard')
        data = {'barcode_id': 99999}
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'error')

    def test_dashboard_delete_identification_barcode_forbidden(self):
        """Test that identification barcodes cannot be deleted"""
        self._authenticate_user(self.school_user)
        
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode='1234567890123456789012345678',
            barcode_type='Identification'
        )
        
        url = reverse('index:api_barcode_dashboard')
        data = {'barcode_id': barcode.id}
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'error')


class BarcodeSerializerTest(TestCase):
    """Test BarcodeSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456',
            barcode_type='Others'
        )

    def test_serializer_fields(self):
        """Test serializer includes all required fields"""
        from index.serializers import BarcodeSerializer
        
        serializer = BarcodeSerializer(self.barcode)
        data = serializer.data
        
        expected_fields = [
            'id', 'barcode_type', 'barcode', 'time_created',
            'usage_count', 'last_used', 'display_name', 'owner',
            'is_owned_by_current_user', 'has_profile_addon'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)

    def test_usage_count_with_usage_record(self):
        """Test usage_count field with existing usage record"""
        from index.serializers import BarcodeSerializer
        
        BarcodeUsage.objects.create(barcode=self.barcode, total_usage=10)
        
        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data['usage_count'], 10)

    def test_usage_count_without_usage_record(self):
        """Test usage_count field without usage record"""
        from index.serializers import BarcodeSerializer
        
        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data['usage_count'], 0)

    def test_display_name_identification(self):
        """Test display name for identification barcode"""
        from index.serializers import BarcodeSerializer
        
        self.barcode.barcode_type = 'Identification'
        self.barcode.save()
        
        serializer = BarcodeSerializer(self.barcode)
        expected = "testuser's identification barcode"
        self.assertEqual(serializer.data['display_name'], expected)

    def test_display_name_dynamic(self):
        """Test display name for dynamic barcode"""
        from index.serializers import BarcodeSerializer
        
        self.barcode.barcode_type = 'DynamicBarcode'
        self.barcode.save()
        
        serializer = BarcodeSerializer(self.barcode)
        expected = "Dynamic Barcode ending with 3456"
        self.assertEqual(serializer.data['display_name'], expected)

    def test_has_profile_addon_true(self):
        """Test has_profile_addon when profile exists"""
        from index.serializers import BarcodeSerializer
        
        BarcodeUserProfile.objects.create(
            linked_barcode=self.barcode,
            name='Test User',
            information_id='TEST123'
        )
        
        serializer = BarcodeSerializer(self.barcode)
        self.assertTrue(serializer.data['has_profile_addon'])

    def test_has_profile_addon_false(self):
        """Test has_profile_addon when profile doesn't exist"""
        from index.serializers import BarcodeSerializer
        
        serializer = BarcodeSerializer(self.barcode)
        self.assertFalse(serializer.data['has_profile_addon'])


class BarcodeCreateSerializerTest(TestCase):
    """Test BarcodeCreateSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.school_group = Group.objects.create(name='School')
        self.user.groups.add(self.school_group)

    def test_validate_barcode_strips_whitespace(self):
        """Test that barcode validation strips whitespace"""
        from index.serializers import BarcodeCreateSerializer
        
        serializer = BarcodeCreateSerializer()
        result = serializer.validate_barcode('  test123  ')
        self.assertEqual(result, 'test123')

    def test_create_dynamic_barcode(self):
        """Test creating dynamic barcode for school user"""
        from index.serializers import BarcodeCreateSerializer
        
        data = {'barcode': '1234567890123456789012345678'}  # 28 digits
        context = {'request': Mock(user=self.user)}
        
        serializer = BarcodeCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        barcode = serializer.save()
        self.assertEqual(barcode.barcode_type, 'DynamicBarcode')
        self.assertEqual(barcode.barcode, '56789012345678')  # Last 14 digits

    def test_create_others_barcode(self):
        """Test creating Others type barcode"""
        from index.serializers import BarcodeCreateSerializer
        
        data = {'barcode': 'regular-barcode-123'}
        context = {'request': Mock(user=self.user)}
        
        serializer = BarcodeCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        barcode = serializer.save()
        self.assertEqual(barcode.barcode_type, 'Others')
        self.assertEqual(barcode.barcode, 'regular-barcode-123')


class UserBarcodeSettingsSerializerTest(TestCase):
    """Test UserBarcodeSettingsSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.user_group = Group.objects.create(name='User')
        self.school_group = Group.objects.create(name='School')

    def test_field_states_user_group(self):
        """Test field states for User group member"""
        from index.serializers import UserBarcodeSettingsSerializer
        
        self.user.groups.add(self.user_group)
        
        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {'request': Mock(user=self.user)}
        
        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        field_states = serializer.data['field_states']
        
        self.assertTrue(field_states['associate_user_profile_disabled'])
        self.assertFalse(field_states['barcode_disabled'])

    def test_field_states_school_group(self):
        """Test field states for School group member"""
        from index.serializers import UserBarcodeSettingsSerializer
        
        self.user.groups.add(self.school_group)
        
        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {'request': Mock(user=self.user)}
        
        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        field_states = serializer.data['field_states']
        
        self.assertFalse(field_states['associate_user_profile_disabled'])
        self.assertFalse(field_states['barcode_disabled'])

    def test_validate_user_group_profile_association(self):
        """Test validation prevents User group from enabling profile association"""
        from index.serializers import UserBarcodeSettingsSerializer
        
        self.user.groups.add(self.user_group)
        
        data = {'associate_user_profile_with_barcode': True}
        context = {'request': Mock(user=self.user)}
        
        serializer = UserBarcodeSettingsSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('associate_user_profile_with_barcode', serializer.errors)

    def test_barcode_choices_school_user(self):
        """Test barcode choices for school user"""
        from index.serializers import UserBarcodeSettingsSerializer
        
        self.user.groups.add(self.school_group)
        
        # Create barcodes
        dynamic_barcode = Barcode.objects.create(
            user=self.user,
            barcode='12345678901234',
            barcode_type='DynamicBarcode'
        )
        
        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {'request': Mock(user=self.user)}
        
        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        choices = serializer.data['barcode_choices']
        
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]['id'], dynamic_barcode.id)
        self.assertEqual(choices[0]['barcode_type'], 'DynamicBarcode')

    def test_barcode_choices_user_type(self):
        """Test barcode choices for User group member (identification only)"""
        from index.serializers import UserBarcodeSettingsSerializer
        
        self.user.groups.add(self.user_group)
        
        # Create identification barcode
        ident_barcode = Barcode.objects.create(
            user=self.user,
            barcode='1234567890123456789012345678',
            barcode_type='Identification'
        )
        
        # Create other barcode (should not appear in choices)
        Barcode.objects.create(
            user=self.user,
            barcode='other123456789',
            barcode_type='Others'
        )
        
        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {'request': Mock(user=self.user)}
        
        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        choices = serializer.data['barcode_choices']
        
        # Should only have identification barcode
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]['id'], ident_barcode.id)
        self.assertEqual(choices[0]['barcode_type'], 'Identification')
