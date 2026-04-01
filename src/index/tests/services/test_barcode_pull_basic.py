from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from index.repositories import (
    BarcodeRepository,
    SettingsRepository,
    TransactionRepository,
)
from index.services.barcode import generate_barcode
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin


class BarcodePullTestBase(DynamoDBTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )

        # Setup settings with pull enabled
        SettingsRepository.update(
            self.school_user.id,
            pull_setting="Enable",
            pull_gender_setting="Male",
        )

        # 1. Male, Shareable, Dynamic (Candidate)
        owner1 = User.objects.create_user("owner1")
        self.bc_male = BarcodeRepository.create(
            user_id=owner1.id,
            barcode_value="male_shareable",
            barcode_type="DynamicBarcode",
            owner_username=owner1.username,
            share_with_others=True,
            profile_gender="Male",
        )

        # 2. Female, Shareable, Dynamic (Wrong Gender)
        owner2 = User.objects.create_user("owner2")
        self.bc_female = BarcodeRepository.create(
            user_id=owner2.id,
            barcode_value="female_shareable",
            barcode_type="DynamicBarcode",
            owner_username=owner2.username,
            share_with_others=True,
            profile_gender="Female",
        )

        # 3. Male, Not Shareable (Wrong Permission)
        owner3 = User.objects.create_user("owner3")
        self.bc_private = BarcodeRepository.create(
            user_id=owner3.id,
            barcode_value="male_private",
            barcode_type="DynamicBarcode",
            owner_username=owner3.username,
            share_with_others=False,
            profile_gender="Male",
        )

        # 4. Male, Owned by user (Candidate)
        self.bc_owned = BarcodeRepository.create(
            user_id=self.school_user.id,
            barcode_value="male_owned",
            barcode_type="Others",
            owner_username=self.school_user.username,
            share_with_others=False,
            profile_gender="Male",
        )


class BarcodePullBasicTest(BarcodePullTestBase):
    def test_pull_basic_candidate(self):
        """Test pulling a valid candidate (Male, Shareable)"""
        with patch(
            "index.services.barcode.generator._timestamp", return_value="20230101000000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        # Should pick bc_male or bc_owned.
        valid_barcodes = []
        if "male_shareable" in result["barcode"]:
            valid_barcodes.append("male_shareable")
        if "male_owned" in result["barcode"]:
            valid_barcodes.append("male_owned")

        self.assertTrue(len(valid_barcodes) > 0, f"Got {result['barcode']}")

        # Check settings updated
        settings = SettingsRepository.get(self.school_user.id)
        active_uuid = settings.get("active_barcode_uuid")
        active_barcode = BarcodeRepository.get_by_uuid(self.school_user.id, active_uuid)
        if not active_barcode:
            # Could be a shared barcode from another user
            shared = BarcodeRepository.get_shared_dynamic_barcodes()
            active_barcode = next(
                (b for b in shared if b["barcode_uuid"] == active_uuid), None
            )
        self.assertIsNotNone(active_barcode)
        self.assertIn(
            active_barcode["barcode"],
            ["male_shareable", "male_owned"],
        )

    def test_pull_wrong_gender(self):
        """Test that female barcode is not pulled"""
        # Delete other candidates to isolate
        BarcodeRepository.delete(
            user_id=self.bc_male["user_id"],
            barcode_uuid=self.bc_male["barcode_uuid"],
        )
        BarcodeRepository.delete(
            user_id=self.bc_owned["user_id"],
            barcode_uuid=self.bc_owned["barcode_uuid"],
        )

        result = generate_barcode(self.school_user)
        # Should fail as no candidates
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_exclude_recently_used_global(self):
        """Test that barcode used by others < 5 mins ago is excluded"""
        # Mark bc_male as used 2 mins ago by setting last_used
        recent_time = (timezone.now() - timedelta(minutes=2)).isoformat()
        BarcodeRepository.update(
            user_id=self.bc_male["user_id"],
            barcode_uuid=self.bc_male["barcode_uuid"],
            last_used=recent_time,
        )

        # Create another valid shared candidate that hasn't been used
        owner_alt = User.objects.create_user("owner_alt")
        BarcodeRepository.create(
            user_id=owner_alt.id,
            barcode_value="male_alt_shareable",
            barcode_type="DynamicBarcode",
            owner_username=owner_alt.username,
            share_with_others=True,
            profile_gender="Male",
        )

        with patch(
            "index.services.barcode.generator._timestamp",
            return_value="20230101000000",
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("male_alt_shareable", result["barcode"])
        self.assertNotIn("male_shareable", result["barcode"])

    def test_pull_sticky_user_history(self):
        """Test that user gets same barcode if used < 10 mins ago, even if globally used recently"""  # noqa: E501
        now = timezone.now()

        # User used bc_male 8 mins ago
        old_time = (now - timedelta(minutes=8)).isoformat()
        TransactionRepository.create(
            user_id=self.school_user.id,
            barcode_uuid=self.bc_male["barcode_uuid"],
            barcode_value=self.bc_male["barcode"],
            time_created=old_time,
        )

        # Also mark it as used globally 2 mins ago (which would normally exclude it)
        recent_time = (now - timedelta(minutes=2)).isoformat()
        BarcodeRepository.update(
            user_id=self.bc_male["user_id"],
            barcode_uuid=self.bc_male["barcode_uuid"],
            last_used=recent_time,
        )

        with patch(
            "index.services.barcode.generator._timestamp", return_value="20230101000000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        # Should be sticky
        self.assertIn("male_shareable", result["barcode"])

    def test_pull_sticky_expired(self):
        """Test that stickiness expires after 10 mins"""
        now = timezone.now()

        # Create another valid shared candidate
        owner_alt = User.objects.create_user("owner_alt2")
        BarcodeRepository.create(
            user_id=owner_alt.id,
            barcode_value="male_alt2_shareable",
            barcode_type="DynamicBarcode",
            owner_username=owner_alt.username,
            share_with_others=True,
            profile_gender="Male",
        )

        # User used bc_male 12 mins ago
        old_time = (now - timedelta(minutes=12)).isoformat()
        TransactionRepository.create(
            user_id=self.school_user.id,
            barcode_uuid=self.bc_male["barcode_uuid"],
            barcode_value=self.bc_male["barcode"],
            time_created=old_time,
        )

        # And it's used globally 2 mins ago (so should be excluded)
        recent_time = (now - timedelta(minutes=2)).isoformat()
        BarcodeRepository.update(
            user_id=self.bc_male["user_id"],
            barcode_uuid=self.bc_male["barcode_uuid"],
            last_used=recent_time,
        )

        # bc_male excluded (recently used), bc_alt2 should be picked
        with patch(
            "index.services.barcode.generator._timestamp",
            return_value="20230101000000",
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("male_alt2_shareable", result["barcode"])
