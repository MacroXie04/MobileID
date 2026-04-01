from unittest.mock import patch

from index.repositories import BarcodeRepository, SettingsRepository
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
        dynamic_barcode = BarcodeRepository.create(
            user_id=self.school_user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.school_user.username,
        )

        SettingsRepository.update(
            self.school_user.id,
            active_barcode_uuid=dynamic_barcode["barcode_uuid"],
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
        other_barcode = BarcodeRepository.create(
            user_id=self.school_user.id,
            barcode_value="static123456789",
            barcode_type="Others",
            owner_username=self.school_user.username,
        )

        SettingsRepository.update(
            self.school_user.id,
            active_barcode_uuid=other_barcode["barcode_uuid"],
        )

        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Others")
        self.assertEqual(result["barcode"], "static123456789")
        self.assertIn("Barcode ending with 6789", result["message"])

    def test_generate_barcode_dynamic_timestamp(self):
        """Test dynamic barcode includes timestamp prefix"""
        dynamic_barcode = BarcodeRepository.create(
            user_id=self.school_user.id,
            barcode_value="12345678901234",
            barcode_type="DynamicBarcode",
            owner_username=self.school_user.username,
        )

        SettingsRepository.update(
            self.school_user.id,
            active_barcode_uuid=dynamic_barcode["barcode_uuid"],
        )

        with patch(
            "index.services.barcode.generator._timestamp", return_value="20231201120000"
        ):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("Dynamic: 1234", result["message"])
