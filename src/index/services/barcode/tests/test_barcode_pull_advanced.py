from unittest.mock import patch

from django.contrib.auth.models import User

from index.repositories import BarcodeRepository, SettingsRepository
from index.services.barcode import generate_barcode
from index.services.barcode.tests.test_barcode_pull_basic import BarcodePullTestBase


class BarcodePullAdvancedTest(BarcodePullTestBase):
    def test_pull_setting_disabled(self):
        """Test that pull logic is skipped when setting is Disable"""
        SettingsRepository.update(
            self.school_user.id,
            pull_setting="Disable",
        )

        # Even though candidates exist, it should fail because no barcode is selected
        # in settings and pull is disabled.
        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_user_with_no_candidates(self):
        """Test that a user with pull enabled but no matching candidates gets error"""
        regular_user = User.objects.create_user("regular", password="pw")

        # Use a gender that has no matching barcodes
        SettingsRepository.update(
            regular_user.id,
            pull_setting="Enable",
            pull_gender_setting="Female",
        )

        # No Female barcodes owned by this user, and bc_female is owned by
        # someone else but is shared -- it will be pulled. Use a non-existent
        # gender to truly have no candidates.
        SettingsRepository.update(
            regular_user.id,
            pull_gender_setting="Unknow",
        )

        result = generate_barcode(regular_user)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_empty_pool_behavior(self):
        """Test behavior when pool is empty and no existing selection"""
        # Delete all candidates
        BarcodeRepository.delete(
            user_id=self.bc_male["user_id"],
            barcode_uuid=self.bc_male["barcode_uuid"],
        )
        BarcodeRepository.delete(
            user_id=self.bc_owned["user_id"],
            barcode_uuid=self.bc_owned["barcode_uuid"],
        )

        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_empty_pool_with_existing_selection(self):
        """Test behavior when pool is empty but user has an existing selection"""
        # Pre-select a barcode
        SettingsRepository.update(
            self.school_user.id,
            active_barcode_uuid=self.bc_male["barcode_uuid"],
        )

        # Make pool empty by gender mismatch
        SettingsRepository.update(
            self.school_user.id,
            pull_gender_setting="Female",
        )

        # Falls back to existing selection (bc_male) even though
        # it doesn't match gender — pull finds no candidate.

        with patch(
            "index.services.barcode.generator._timestamp", return_value="20230101000000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("male_shareable", result["barcode"])

    def test_pull_gender_unknow(self):
        """Test pulling with gender 'Unknow'"""
        SettingsRepository.update(
            self.school_user.id,
            pull_gender_setting="Unknow",
        )

        # Create an Unknow gender barcode
        owner_unknow = User.objects.create_user("owner_unknow")
        BarcodeRepository.create(
            user_id=owner_unknow.id,
            barcode_value="unknow_shareable",
            barcode_type="DynamicBarcode",
            owner_username=owner_unknow.username,
            share_with_others=True,
            profile_gender="Unknow",
        )

        # Should pick bc_unknow (others are Male/Female)
        with patch(
            "index.services.barcode.generator._timestamp", return_value="20230101000000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("unknow_shareable", result["barcode"])
