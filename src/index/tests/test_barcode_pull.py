from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.utils import timezone

from index.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
    UserBarcodePullSettings,
    BarcodeUserProfile,
    Transaction,
)
from index.services.barcode import generate_barcode


class BarcodePullTest(TestCase):
    def setUp(self):
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )
        self.school_group = Group.objects.create(name="School")
        self.school_user.groups.add(self.school_group)

        # Setup pull settings
        self.pull_settings = UserBarcodePullSettings.objects.create(
            user=self.school_user,
            pull_setting="Enable",
            gender_setting="Male",
        )
        
        # Setup user settings
        self.user_settings = UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=None
        )

        # Create some barcodes
        # 1. Male, Shareable, Dynamic (Candidate)
        self.bc_male = Barcode.objects.create(
            user=User.objects.create_user("owner1"),
            barcode="male_shareable",
            barcode_type="DynamicBarcode",
            share_with_others=True,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=self.bc_male,
            gender_barcode="Male"
        )

        # 2. Female, Shareable, Dynamic (Wrong Gender)
        self.bc_female = Barcode.objects.create(
            user=User.objects.create_user("owner2"),
            barcode="female_shareable",
            barcode_type="DynamicBarcode",
            share_with_others=True,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=self.bc_female,
            gender_barcode="Female"
        )

        # 3. Male, Not Shareable (Wrong Permission)
        self.bc_private = Barcode.objects.create(
            user=User.objects.create_user("owner3"),
            barcode="male_private",
            barcode_type="DynamicBarcode",
            share_with_others=False,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=self.bc_private,
            gender_barcode="Male"
        )

        # 4. Male, Owned by user (Candidate)
        self.bc_owned = Barcode.objects.create(
            user=self.school_user,
            barcode="male_owned",
            barcode_type="Others", # Owned can be any type
            share_with_others=False,
        )
        BarcodeUserProfile.objects.create(
            linked_barcode=self.bc_owned,
            gender_barcode="Male"
        )

    def test_pull_basic_candidate(self):
        """Test pulling a valid candidate (Male, Shareable)"""
        # Ensure no usage history
        
        with patch("index.services.barcode._timestamp", return_value="20230101000000"):
            result = generate_barcode(self.school_user)
        
        self.assertEqual(result["status"], "success")
        # Should pick bc_male or bc_owned. 
        # Since random, could be either. But let's check if it's one of them.
        # Note: generate_barcode returns full barcode string.
        # For Dynamic: timestamp + barcode
        # For Others: barcode
        
        valid_barcodes = []
        if "male_shareable" in result["barcode"]:
            valid_barcodes.append("male_shareable")
        if "male_owned" in result["barcode"]:
            valid_barcodes.append("male_owned")
            
        self.assertTrue(len(valid_barcodes) > 0, f"Got {result['barcode']}")
        
        # Check settings updated
        self.user_settings.refresh_from_db()
        self.assertIn(self.user_settings.barcode.barcode, ["male_shareable", "male_owned"])

    def test_pull_wrong_gender(self):
        """Test that female barcode is not pulled"""
        # Delete other candidates to isolate
        self.bc_male.delete()
        self.bc_owned.delete()
        
        result = generate_barcode(self.school_user)
        # Should fail as no candidates
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_exclude_recently_used_global(self):
        """Test that barcode used by others < 5 mins ago is excluded"""
        # Mark bc_male as used 2 mins ago
        now = timezone.now()
        bu = BarcodeUsage.objects.create(
            barcode=self.bc_male
        )
        BarcodeUsage.objects.filter(pk=bu.pk).update(last_used=now - timedelta(minutes=2))
        
        # bc_owned is still available
        with patch("index.services.barcode._timestamp", return_value="20230101000000"):
            result = generate_barcode(self.school_user)
            
        self.assertEqual(result["status"], "success")
        self.assertIn("male_owned", result["barcode"])
        self.assertNotIn("male_shareable", result["barcode"])

    def test_pull_sticky_user_history(self):
        """Test that user gets same barcode if used < 10 mins ago, even if globally used recently"""
        now = timezone.now()
        
        # User used bc_male 8 mins ago
        txn = Transaction.objects.create(
            user=self.school_user,
            barcode_used=self.bc_male
        )
        Transaction.objects.filter(pk=txn.pk).update(time_created=now - timedelta(minutes=8))
        
        # Also mark it as used globally 2 mins ago (which would normally exclude it)
        bu = BarcodeUsage.objects.create(
            barcode=self.bc_male
        )
        BarcodeUsage.objects.filter(pk=bu.pk).update(last_used=now - timedelta(minutes=2))
        
        with patch("index.services.barcode._timestamp", return_value="20230101000000"):
            result = generate_barcode(self.school_user)
            
        self.assertEqual(result["status"], "success")
        # Should be sticky
        self.assertIn("male_shareable", result["barcode"])

    def test_pull_sticky_expired(self):
        """Test that stickiness expires after 10 mins"""
        now = timezone.now()
        
        # User used bc_male 12 mins ago
        txn = Transaction.objects.create(
            user=self.school_user,
            barcode_used=self.bc_male
        )
        Transaction.objects.filter(pk=txn.pk).update(time_created=now - timedelta(minutes=12))
        
        # And it's used globally 2 mins ago (so should be excluded)
        bu = BarcodeUsage.objects.create(
            barcode=self.bc_male
        )
        BarcodeUsage.objects.filter(pk=bu.pk).update(last_used=now - timedelta(minutes=2))
        
        # Only bc_owned should be available
        with patch("index.services.barcode._timestamp", return_value="20230101000000"):
            result = generate_barcode(self.school_user)
            
        self.assertEqual(result["status"], "success")
        self.assertIn("male_owned", result["barcode"])

    def test_pull_setting_disabled(self):
        """Test that pull logic is skipped when setting is Disable"""
        self.pull_settings.pull_setting = "Disable"
        self.pull_settings.save()
        
        # Even though candidates exist, it should fail because no barcode is selected in settings
        # and pull is disabled.
        result = generate_barcode(self.school_user)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_user_not_school(self):
        """Test that pull logic is skipped for non-School users"""
        # Create a regular user with pull enabled (though UI might prevent this, backend should handle it)
        regular_user = User.objects.create_user("regular", password="pw")
        user_group, _ = Group.objects.get_or_create(name="User")
        regular_user.groups.add(user_group)
        
        # Case 1: User in 'User' group.
        UserBarcodePullSettings.objects.create(
            user=regular_user,
            pull_setting="Enable",
            gender_setting="Male"
        )
        UserBarcodeSettings.objects.create(user=regular_user)
        
        # generate_barcode for 'User' group forces Identification barcode, ignoring pull settings.
        result = generate_barcode(regular_user)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Identification")
        
        # Case 2: User with no group (Permission Denied)
        no_group_user = User.objects.create_user("nogroup", password="pw")
        result = generate_barcode(no_group_user)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Permission Denied.")

    def test_pull_empty_pool_behavior(self):
        """Test behavior when pool is empty and no existing selection"""
        # Delete all candidates
        self.bc_male.delete()
        self.bc_owned.delete()
        
        result = generate_barcode(self.school_user)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_pull_empty_pool_with_existing_selection(self):
        """Test behavior when pool is empty but user has an existing selection"""
        # Pre-select a barcode
        self.user_settings.barcode = self.bc_male
        self.user_settings.save()
        
        # Make pool empty by gender mismatch
        self.pull_settings.gender_setting = "Female"
        self.pull_settings.save()
        
        # Should fall back to existing selection (bc_male) even though it doesn't match gender?
        # The pull logic fails to find candidate, so it leaves settings.barcode alone.
        # Then it uses settings.barcode.
        
        with patch("index.services.barcode._timestamp", return_value="20230101000000"):
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
            linked_barcode=bc_unknow,
            gender_barcode="Unknow"
        )
        
        # Should pick bc_unknow (others are Male/Female)
        with patch("index.services.barcode._timestamp", return_value="20230101000000"):
            result = generate_barcode(self.school_user)
            
        self.assertEqual(result["status"], "success")
        self.assertIn("unknow_shareable", result["barcode"])
