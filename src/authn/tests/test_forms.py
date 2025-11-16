from django.test import TestCase

from authn.api.webauthn import UserRegisterForm


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
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
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
            "user_profile_img_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, "testuser")
        self.assertTrue(hasattr(user, "userprofile"))
        self.assertIsNotNone(user.userprofile.user_profile_img)

