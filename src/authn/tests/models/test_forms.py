from authn.api.webauthn import UserRegisterForm
from django.contrib.auth.models import User
from django.test import TestCase


class UserFormTest(TestCase):
    """Test UserRegisterForm functionality"""

    def test_form_valid_data(self):
        form_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123",
            "name": "Test User",
            "information_id": "TEST123",
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_password_mismatch(self):
        form_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "differentpass",
            "name": "Test User",
            "information_id": "TEST123",
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_allows_single_character_password(self):
        form_data = {
            "username": "weakpassuser",
            "password1": "1",
            "password2": "1",
            "name": "Weak Pass User",
            "information_id": "TEST123",
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_password_required(self):
        form_data = {
            "username": "testuser",
            "password1": "",
            "password2": "",
            "name": "Test User",
            "information_id": "TEST123",
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)
        self.assertIn("password2", form.errors)

    def test_form_base64_validation(self):
        form_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123",
            "name": "Test User",
            "information_id": "TEST123",
            "user_profile_img_base64": "invalid-base64",
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("user_profile_img_base64", form.errors)

    def test_form_base64_data_uri_cleanup(self):
        form_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123",
            "name": "Test User",
            "information_id": "TEST123",
            "user_profile_img_base64": "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+"
            "hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_b64 = form.cleaned_data["user_profile_img_base64"]
        self.assertFalse(cleaned_b64.startswith("data:"))

    def test_form_save_with_avatar(self):
        form_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123",
            "name": "Test User",
            "information_id": "TEST123",
            "user_profile_img_base64": (
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+"  # noqa: E501
                "hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            ),
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(hasattr(user, "userprofile"))
        self.assertIsNotNone(user.userprofile.user_profile_img)

    def test_form_duplicate_username_invalid(self):
        User.objects.create_user(username="testuser", password="pass123")
        form_data = {
            "username": "testuser",
            "password1": "1",
            "password2": "1",
            "name": "Test User",
            "information_id": "TEST123",
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
