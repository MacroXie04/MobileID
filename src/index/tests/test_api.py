from authn.models import UserProfile
from authn.services.webauthn import create_user_profile
from django.contrib.auth.models import User, Group
from django.urls import reverse
from index.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
    UserBarcodePullSettings,
    BarcodeUserProfile,
)
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class GenerateBarcodeAPITest(APITestCase):
    """Test GenerateBarcodeAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.user_group = Group.objects.create(name="User")
        self.user.groups.add(self.user_group)

        create_user_profile(self.user, "Test User", "TEST123", None)

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_generate_barcode_success(self):
        """Test successful barcode generation"""
        url = reverse("index:api_generate_barcode")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["barcode_type"], "Identification")

    def test_generate_barcode_unauthenticated(self):
        """Test barcode generation without authentication"""
        self.client.credentials()  # Remove authentication

        url = reverse("index:api_generate_barcode")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BarcodeDashboardAPITest(APITestCase):
    """Test BarcodeDashboardAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )
        self.user_user = User.objects.create_user(
            username="regularuser", password="testpass123"
        )

        # Create groups
        self.school_group = Group.objects.create(name="School")
        self.user_group = Group.objects.create(name="User")

        # Assign users to groups - School users should NOT be in User group
        self.school_user.groups.add(self.school_group)
        self.user_user.groups.add(self.user_group)

        # Don't use create_user_profile as it adds users to User group automatically  # noqa: E501
        # Create profiles manually for School user
        UserProfile.objects.create(
            user=self.school_user,
            name="School User",
            information_id="SCHOOL123",
        )

        create_user_profile(self.user_user, "Regular User", "USER123", None)

    def _authenticate_user(self, user):
        """Helper to authenticate a user"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_dashboard_get_school_user(self):
        """Test getting dashboard data for school user"""
        self._authenticate_user(self.school_user)

        # Create some barcodes
        _ = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )
        _ = Barcode.objects.create(
            user=self.school_user,
            barcode="static123456789",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("settings", response.data)
        self.assertIn("barcodes", response.data)
        self.assertTrue(response.data["is_school_group"])
        self.assertFalse(response.data["is_user_group"])

        # Should have 2 barcodes
        self.assertEqual(len(response.data["barcodes"]), 2)

    def test_dashboard_get_regular_user_forbidden(self):
        """Test that regular users cannot access dashboard"""
        self._authenticate_user(self.user_user)

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("User type accounts cannot access", response.data["detail"])

    def test_dashboard_post_update_settings(self):
        """Test updating barcode settings"""
        self._authenticate_user(self.school_user)

        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {
            "barcode": barcode.id,
            "associate_user_profile_with_barcode": False,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check settings were updated
        settings = UserBarcodeSettings.objects.get(user=self.school_user)
        self.assertEqual(settings.barcode, barcode)

    def test_dashboard_put_create_barcode(self):
        """Test creating new barcode"""
        self._authenticate_user(self.school_user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": "newbarcode123456789"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")

        # Check barcode was created
        barcode = Barcode.objects.get(barcode="newbarcode123456789")
        self.assertEqual(barcode.user, self.school_user)
        self.assertEqual(barcode.barcode_type, "Others")

    def test_dashboard_put_create_dynamic_barcode(self):
        """Test creating dynamic barcode (28 digits)"""
        self._authenticate_user(self.school_user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": "1234567890123456789012345678"}  # 28 digits

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check barcode was created as dynamic with last 14 digits
        barcode = Barcode.objects.get(
            user=self.school_user, barcode_type="DynamicBarcode"
        )
        self.assertEqual(barcode.barcode, "56789012345678")  # Last 14 digits

    def test_dashboard_delete_barcode(self):
        """Test deleting barcode"""
        self._authenticate_user(self.school_user)

        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="deleteme123456789",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": barcode.id}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check barcode was deleted
        self.assertFalse(Barcode.objects.filter(id=barcode.id).exists())

    def test_dashboard_delete_barcode_not_found(self):
        """Test deleting non-existent barcode"""
        self._authenticate_user(self.school_user)

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": 99999}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")

    def test_dashboard_patch_update_share_and_daily_limit(self):
        """Test PATCH to update share flag and daily usage limit"""
        self._authenticate_user(self.school_user)
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="patchbar12345678",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        # Update share_with_others using string truthy and set daily limit
        data = {
            "barcode_id": barcode.id,
            "share_with_others": "true",
            "daily_usage_limit": 5,
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        barcode.refresh_from_db()
        self.assertTrue(barcode.share_with_others)
        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.daily_usage_limit, 5)

    def test_dashboard_patch_invalid_daily_limit(self):
        """Test PATCH with invalid daily limit values"""
        self._authenticate_user(self.school_user)
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="patchbarinvalid",
            barcode_type="Others",
        )

        url = reverse("index:api_barcode_dashboard")
        # Negative number
        response = self.client.patch(
            url,
            {"barcode_id": barcode.id, "daily_usage_limit": -1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Non-integer
        response = self.client.patch(
            url,
            {"barcode_id": barcode.id, "daily_usage_limit": "not-a-number"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_delete_identification_barcode_forbidden(self):
        """Test that identification barcodes cannot be deleted"""
        self._authenticate_user(self.school_user)

        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode_id": barcode.id}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")

    def test_dashboard_get_includes_pull_settings(self):
        """Test that GET dashboard includes pull_settings in response"""
        self._authenticate_user(self.school_user)

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("pull_settings", response.data)
        self.assertEqual(response.data["pull_settings"]["pull_setting"], "Disable")
        self.assertEqual(response.data["pull_settings"]["gender_setting"], "Unknow")

    def test_dashboard_post_update_pull_settings(self):
        """Test updating pull settings via POST"""
        self._authenticate_user(self.school_user)

        url = reverse("index:api_barcode_dashboard")
        data = {
            "pull_settings": {
                "pull_setting": "Enable",
                "gender_setting": "Male",
            }
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("pull_settings", response.data)
        self.assertEqual(response.data["pull_settings"]["pull_setting"], "Enable")
        self.assertEqual(response.data["pull_settings"]["gender_setting"], "Male")

        # Check settings were updated in database
        pull_settings = UserBarcodePullSettings.objects.get(user=self.school_user)
        self.assertEqual(pull_settings.pull_setting, "Enable")
        self.assertEqual(pull_settings.gender_setting, "Male")

    def test_dashboard_post_barcode_selection_disabled_when_pull_enabled(self):
        """Test that barcode selection is rejected when pull_setting is enabled"""  # noqa: E501
        self._authenticate_user(self.school_user)

        # Enable pull setting
        UserBarcodePullSettings.objects.create(
            user=self.school_user, pull_setting="Enable", gender_setting="Male"
        )

        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": barcode.id}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("barcode", response.data["errors"])
        self.assertIn(
            "disabled when pull setting is enabled",
            response.data["errors"]["barcode"][0],
        )

    def test_dashboard_get_field_states_barcode_disabled_when_pull_enabled(
        self,
    ):
        """Test that field_states shows barcode_disabled when pull_setting is enabled"""  # noqa: E501
        self._authenticate_user(self.school_user)

        # Enable pull setting
        UserBarcodePullSettings.objects.create(
            user=self.school_user,
            pull_setting="Enable",
            gender_setting="Female",
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        field_states = response.data["settings"]["field_states"]
        self.assertTrue(field_states["barcode_disabled"])

    def test_dashboard_get_field_states_barcode_enabled_when_pull_disabled(
        self,
    ):
        """Test that field_states shows barcode_disabled=False when pull_setting is disabled"""  # noqa: E501
        self._authenticate_user(self.school_user)

        # Ensure pull setting is disabled
        UserBarcodePullSettings.objects.create(
            user=self.school_user,
            pull_setting="Disable",
            gender_setting="Unknow",
        )

        url = reverse("index:api_barcode_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        field_states = response.data["settings"]["field_states"]
        self.assertFalse(field_states["barcode_disabled"])

    def test_dashboard_post_can_update_barcode_when_pull_disabled(self):
        """Test that barcode can be updated when pull_setting is disabled"""
        self._authenticate_user(self.school_user)

        # Ensure pull setting is disabled
        UserBarcodePullSettings.objects.create(
            user=self.school_user,
            pull_setting="Disable",
            gender_setting="Unknow",
        )

        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        url = reverse("index:api_barcode_dashboard")
        data = {"barcode": barcode.id}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check settings were updated
        settings = UserBarcodeSettings.objects.get(user=self.school_user)
        self.assertEqual(settings.barcode, barcode)

    def test_dashboard_post_auto_clear_barcode_when_pull_enabled(self):
        """Test that barcode is automatically cleared when pull_setting is enabled"""  # noqa: E501
        self._authenticate_user(self.school_user)

        # Create a barcode and set it in settings
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )
        settings = UserBarcodeSettings.objects.create(
            user=self.school_user, barcode=barcode
        )

        url = reverse("index:api_barcode_dashboard")
        # Enable pull setting and include barcode in the same request
        data = {
            "pull_settings": {
                "pull_setting": "Enable",
                "gender_setting": "Male",
            },
            "barcode": barcode.id,
        }

        response = self.client.post(url, data, format="json")

        # Should succeed (200) instead of failing (400)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Check that barcode was cleared in settings
        settings.refresh_from_db()
        self.assertIsNone(settings.barcode)

        # Check that pull settings were updated
        pull_settings = UserBarcodePullSettings.objects.get(user=self.school_user)
        self.assertEqual(pull_settings.pull_setting, "Enable")
        self.assertEqual(pull_settings.gender_setting, "Male")

        # Check response shows barcode as None
        self.assertIsNone(response.data["settings"]["barcode"])


class ActiveProfileAPITest(APITestCase):
    """Tests for ActiveProfileAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )
        self.regular_user = User.objects.create_user(
            username="regularuser", password="testpass123"
        )
        school_group = Group.objects.create(name="School")
        user_group = Group.objects.create(name="User")
        self.school_user.groups.add(school_group)
        self.regular_user.groups.add(user_group)

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_non_school_user_gets_none(self):
        self._auth(self.regular_user)
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["profile_info"])

    def test_school_user_with_linked_profile(self):
        self._auth(self.school_user)
        # Create barcode and link settings and profile
        bc = Barcode.objects.create(
            user=self.school_user,
            barcode="activeprof123456",
            barcode_type="Others",
        )
        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=bc,
            associate_user_profile_with_barcode=True,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=bc,
            name="School User",
            information_id="SCHOOL123",
            user_profile_img=None,
        )
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(resp.data["profile_info"])
        self.assertEqual(resp.data["profile_info"]["name"], "School User")
        self.assertEqual(resp.data["profile_info"]["information_id"], "SCHOOL123")
        self.assertFalse(resp.data["profile_info"]["has_avatar"])

    def test_school_user_with_avatar_adds_data_uri(self):
        self._auth(self.school_user)
        bc = Barcode.objects.create(
            user=self.school_user,
            barcode="activeprofavatar",
            barcode_type="Others",
        )
        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=bc,
            associate_user_profile_with_barcode=True,
        )
        # Store raw base64 without data URI; endpoint should prefix data:image/png  # noqa: E501
        BarcodeUserProfile.objects.create(
            linked_barcode=bc,
            name="Avatar User",
            information_id="AVT123",
            user_profile_img="dGVzdA==",
        )
        url = reverse("index:api_active_profile")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_info"]["has_avatar"])
        self.assertTrue(
            resp.data["profile_info"]["avatar_data"].startswith("data:image")
        )


class TransferDynamicBarcodeAPITest(APITestCase):
    """Tests for TransferDynamicBarcodeAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )
        self.regular_user = User.objects.create_user(
            username="regularuser", password="testpass123"
        )
        school_group = Group.objects.create(name="School")
        user_group = Group.objects.create(name="User")
        self.school_user.groups.add(school_group)
        self.regular_user.groups.add(user_group)

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def _get_sample_html(self):
        """Return sample HTML that can be parsed"""
        return """
        <html>
        <h4 class="white-h4" style="margin-top: 10px;">John Doe</h4>
        <h4 id="student-id">12345</h4>
        <img src="data:image/jpeg;base64,dGVzdGltYWdl" />
        <script>
        var formattedTimestamp + "12345678901234"
        </script>
        </html>
        """

    def test_transfer_success(self):
        """Test successful HTML transfer and barcode creation"""
        self._auth(self.school_user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("barcode", response.data)

        # Check barcode was created
        barcode = Barcode.objects.get(barcode="12345678901234")
        self.assertEqual(barcode.user, self.school_user)
        self.assertEqual(barcode.barcode_type, "DynamicBarcode")

        # Check profile was created
        profile = BarcodeUserProfile.objects.get(linked_barcode=barcode)
        self.assertEqual(profile.name, "John Doe")
        self.assertEqual(profile.information_id, "12345")
        self.assertEqual(profile.user_profile_img, "dGVzdGltYWdl")

    def test_transfer_non_school_user_forbidden(self):
        """Test that non-school users cannot use transfer endpoint"""
        self._auth(self.regular_user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["status"], "error")

    def test_transfer_missing_html(self):
        """Test that missing HTML returns error"""
        self._auth(self.school_user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("html", response.data["errors"])

    def test_transfer_unparseable_html(self):
        """Test that unparseable HTML returns appropriate errors"""
        self._auth(self.school_user)

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": "<html><body>No barcode info here</body></html>"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        # Should have errors for missing fields
        errors = response.data["errors"]
        self.assertTrue(
            "barcode" in errors or "name" in errors or "information_id" in errors
        )

    def test_transfer_duplicate_barcode(self):
        """Test that transferring duplicate barcode fails"""
        self._auth(self.school_user)

        # Create existing barcode
        Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error can be in errors dict or at top level from serializer
        self.assertTrue("errors" in response.data or "barcode" in response.data)

    def test_transfer_unauthenticated(self):
        """Test that unauthenticated users cannot access endpoint"""
        url = reverse("index:api_transfer_dynamic_barcode")
        data = {"html": self._get_sample_html()}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
