from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from index.models import (
    Barcode,
    BarcodeUsage,
    Transaction,
    UserBarcodeSettings,
)
from index.services.barcode import generate_barcode
from index.tests.services.test_barcode_service import BarcodeServiceTestBase


class BarcodeGenerateServiceTest(BarcodeServiceTestBase):
    """Test barcode generation service functions"""

    def _set_identification_barcode(self):
        barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )
        UserBarcodeSettings.objects.create(user=self.school_user, barcode=barcode)
        return barcode

    def test_generate_barcode_no_selection(self):
        """Test barcode generation with no barcode selected"""
        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_generate_barcode_dynamic(self):
        """Test barcode generation with dynamic barcode selected"""
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        UserBarcodeSettings.objects.create(
            user=self.school_user, barcode=dynamic_barcode
        )

        with patch(
            "index.services.barcode.generator._timestamp", return_value="20231201120000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "DynamicBarcode")
        self.assertEqual(result["barcode"], "2023120112000012345678901234")
        self.assertIn("Dynamic: 1234", result["message"])

    def test_generate_barcode_others(self):
        """Test barcode generation with Others barcode selected"""
        other_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="static123456789",
            barcode_type="Others",
        )

        UserBarcodeSettings.objects.create(user=self.school_user, barcode=other_barcode)

        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Others")
        self.assertEqual(result["barcode"], "static123456789")
        self.assertIn("Barcode ending with 6789", result["message"])

    def test_generate_barcode_dynamic_timestamp(self):
        """Test dynamic barcode includes timestamp prefix"""
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=dynamic_barcode,
        )

        with patch(
            "index.services.barcode.generator._timestamp", return_value="20231201120000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("Dynamic: 1234", result["message"])

    def test_generate_identification_first_use_tracks_usage(self):
        """Test first Identification generate creates usage on the rotated barcode."""
        original_barcode = self._set_identification_barcode()

        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Identification")
        self.assertFalse(Barcode.objects.filter(pk=original_barcode.pk).exists())

        current_barcode = Barcode.objects.get(
            user=self.school_user,
            barcode_type="Identification",
        )
        usage = BarcodeUsage.objects.get(barcode=current_barcode)
        self.assertEqual(usage.total_usage, 1)
        self.assertEqual(
            Transaction.objects.filter(
                user=self.school_user,
                barcode_used=current_barcode,
            ).count(),
            1,
        )

    def test_generate_identification_after_5_minutes_preserves_cumulative_usage(self):
        """Test repeated Identification generate after cooldown increments usage."""
        self._set_identification_barcode()

        first_result = generate_barcode(self.school_user)
        self.assertEqual(first_result["status"], "success")

        current_barcode = Barcode.objects.get(
            user=self.school_user,
            barcode_type="Identification",
        )
        old_time = timezone.now() - timedelta(minutes=6)
        BarcodeUsage.objects.filter(barcode=current_barcode).update(last_used=old_time)
        Transaction.objects.filter(
            user=self.school_user,
            barcode_used=current_barcode,
        ).update(time_created=old_time)

        second_result = generate_barcode(self.school_user)

        self.assertEqual(second_result["status"], "success")
        self.assertEqual(
            Barcode.objects.filter(
                user=self.school_user,
                barcode_type="Identification",
            ).count(),
            1,
        )

        rotated_barcode = Barcode.objects.get(
            user=self.school_user,
            barcode_type="Identification",
        )
        usage = BarcodeUsage.objects.get(barcode=rotated_barcode)
        self.assertEqual(usage.total_usage, 2)
        self.assertEqual(
            Transaction.objects.filter(
                user=self.school_user,
                barcode_used=rotated_barcode,
            ).count(),
            1,
        )

    def test_generate_identification_within_5_minutes_keeps_cumulative_usage(self):
        """Test repeated Identification generate within cooldown does not increment."""
        self._set_identification_barcode()

        first_result = generate_barcode(self.school_user)
        self.assertEqual(first_result["status"], "success")

        current_barcode = Barcode.objects.get(
            user=self.school_user,
            barcode_type="Identification",
        )
        first_usage = BarcodeUsage.objects.get(barcode=current_barcode)

        second_result = generate_barcode(self.school_user)

        self.assertEqual(second_result["status"], "success")
        self.assertEqual(
            Barcode.objects.filter(
                user=self.school_user,
                barcode_type="Identification",
            ).count(),
            1,
        )

        rotated_barcode = Barcode.objects.get(
            user=self.school_user,
            barcode_type="Identification",
        )
        usage = BarcodeUsage.objects.get(barcode=rotated_barcode)
        self.assertEqual(usage.total_usage, 1)
        self.assertEqual(usage.last_used, first_usage.last_used)
        self.assertEqual(
            Transaction.objects.filter(
                user=self.school_user,
                barcode_used=rotated_barcode,
            ).count(),
            0,
        )
