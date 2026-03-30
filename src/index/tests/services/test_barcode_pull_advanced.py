from unittest.mock import patch

from django.contrib.auth.models import User

from index.models import (
    Barcode,
    BarcodeUserProfile,
    UserBarcodePullSettings,
    UserBarcodeSettings,
)
from index.services.barcode import generate_barcode
from index.tests.services.test_barcode_pull_basic import BarcodePullTestBase


class BarcodePullAdvancedTest(BarcodePullTestBase):
    def test_pull_setting_disabled(self):
        """Test that pull logic is skipped when setting is Disable"""
        self.pull_settings.pull_setting = "Disable"
        self.pull_settings.save()

        # Even though candidates exist, it should fail because no barcode is selected in settings  # noqa: E501
        # and pull is disabled.
        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_user_with_no_candidates(self):
        """Test that a user with pull enabled but no matching candidates gets error"""
        regular_user = User.objects.create_user("regular", password="pw")

        # Use a gender that has no matching barcodes
        UserBarcodePullSettings.objects.create(
            user=regular_user, pull_setting="Enable", gender_setting="Female"
        )
        UserBarcodeSettings.objects.create(user=regular_user)

        # No Female barcodes owned by this user, and bc_female is owned by
        # someone else but is shared — it will be pulled. Use a non-existent
        # gender to truly have no candidates.
        UserBarcodePullSettings.objects.filter(user=regular_user).update(
            gender_setting="Unknow"
        )

        result = generate_barcode(regular_user)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_empty_pool_behavior(self):
        """Test behavior when pool is empty and no existing selection"""
        # Delete all candidates
        self.bc_male.delete()
        self.bc_owned.delete()

        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_empty_pool_with_existing_selection(self):
        """Test behavior when pool is empty but user has an existing selection"""  # noqa: E501
        # Pre-select a barcode
        self.user_settings.barcode = self.bc_male
        self.user_settings.save()

        # Make pool empty by gender mismatch
        self.pull_settings.gender_setting = "Female"
        self.pull_settings.save()

        # Should fall back to existing selection (bc_male) even though it doesn't match gender?  # noqa: E501
        # The pull logic fails to find candidate, so it leaves settings.barcode alone.  # noqa: E501
        # Then it uses settings.barcode.

        with patch(
            "index.services.barcode.generator._timestamp", return_value="20230101000000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("male_shareable", result["barcode"])

    def test_pull_gender_unknow(self):
        """Test pulling with gender 'Unknow'"""
        self.pull_settings.gender_setting = "Unknow"
        self.pull_settings.save()

        # Create an Unknow gender barcode
        bc_unknow = Barcode.objects.create(
            user=User.objects.create_user("owner_unknow"),
            barcode="unknow_shareable",
            barcode_type="DynamicBarcode",
            share_with_others=True,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=bc_unknow, gender_barcode="Unknow"
        )

        # Should pick bc_unknow (others are Male/Female)
        with patch(
            "index.services.barcode.generator._timestamp", return_value="20230101000000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("unknow_shareable", result["barcode"])
