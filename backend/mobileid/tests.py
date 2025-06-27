from django.test import TestCase
from django.contrib.auth.models import User
from mobileid.models import UserProfile, UserBarcodeSettings

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

class StudentInformationModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create student information for the user
        self.student_info = UserProfile.objects.create(
            user=self.user,
            name='Test Student',
            student_id='12345678',
            user_profile_img=''  # Empty string instead of None
        )

    def test_student_info_creation(self):
        """Test that student information can be created"""
        self.assertEqual(self.student_info.user, self.user)
        self.assertEqual(self.student_info.name, 'Test Student')
        self.assertEqual(self.student_info.id, '12345678')
