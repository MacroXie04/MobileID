from authn.models import UserProfile
from authn.services.webauthn import create_user_profile
from django.contrib.auth.models import Group, User
from django.test import TestCase


class UserProfileServiceTest(TestCase):
    """Test user profile service functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_user_profile_success(self):
        """Test successful user profile creation"""
        name = "Test User"
        info_id = "TEST123"
        avatar_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+"
            "hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )

        returned_user = create_user_profile(self.user, name, info_id, avatar_b64)

        self.assertEqual(returned_user, self.user)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.name, name)
        self.assertEqual(profile.information_id, info_id)
        self.assertEqual(profile.user_profile_img, avatar_b64)
        self.assertTrue(self.user.groups.filter(name="User").exists())

    def test_create_user_profile_without_avatar(self):
        """Test user profile creation without avatar"""
        name = "Test User"
        info_id = "TEST123"

        returned_user = create_user_profile(self.user, name, info_id, None)

        self.assertEqual(returned_user, self.user)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.name, name)
        self.assertEqual(profile.information_id, info_id)
        self.assertIsNone(profile.user_profile_img)

    def test_create_user_profile_group_creation(self):
        """Test that User group is created if it doesn't exist"""
        Group.objects.filter(name="User").delete()

        create_user_profile(self.user, "Test", "ID123", None)

        self.assertTrue(self.user.groups.filter(name="User").exists())
