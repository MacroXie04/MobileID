from unittest.mock import patch

from index.models import (
    Barcode,
    UserBarcodeSettings,
)
from index.services.barcode import generate_barcode
from index.tests.services.test_barcode_service import BarcodeServiceTestBase


class BarcodeGenerateServiceTest(BarcodeServiceTestBase):
    """Test barcode generation service functions"""

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
