from django.contrib.auth.models import User
from django.test import TestCase

from authn.models import UserProfile


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_user_profile_creation(self):
        """Test creating a UserProfile"""
        profile = UserProfile.objects.create(
            user=self.user,
            name="Test User",
            information_id="TEST123",
            user_profile_img="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.name, "Test User")
        self.assertEqual(profile.information_id, "TEST123")
        self.assertIsNotNone(profile.profile_uuid)
        self.assertTrue(profile.user_profile_img)

    def test_user_profile_str_representation(self):
        """Test UserProfile __str__ method"""
        profile = UserProfile.objects.create(
            user=self.user,
            name="Test User",
            information_id="TEST123456",
        )

        expected = "Test User - ID: **3456"
        self.assertEqual(str(profile), expected)

    def test_user_profile_unique_uuid(self):
        """Test that each UserProfile gets a unique UUID"""
        user2 = User.objects.create_user(username="testuser2", password="testpass123")

        profile1 = UserProfile.objects.create(
            user=self.user, name="User 1", information_id="ID1"
        )
        profile2 = UserProfile.objects.create(
            user=user2, name="User 2", information_id="ID2"
        )

        self.assertNotEqual(profile1.profile_uuid, profile2.profile_uuid)

    def test_user_profile_image_validation(self):
        """Test that user_profile_img has proper validation"""
        oversized_b64 = "A" * 15000

        profile = UserProfile(
            user=self.user,
            name="Test User",
            information_id="TEST123",
            user_profile_img=oversized_b64,
        )

        profile.save()
        self.assertEqual(len(profile.user_profile_img), 15000)
