from django.contrib.auth.models import User
from django.test import TestCase
from index.models import (
    Barcode,
    BarcodeUsage,
    Transaction,
)
from index.services.usage_limit import UsageLimitService
from index.services.transfer_barcode import TransferBarcodeParser


class UsageLimitServiceTest(TestCase):
    """Unit tests for UsageLimitService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="limituser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="limit-123456", barcode_type="Others"
        )

    def test_check_daily_limit_no_record_or_zero_limit(self):
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        self.assertIsNone(msg)
        # Create usage with zero limit
        BarcodeUsage.objects.create(barcode=self.barcode, daily_usage_limit=0)
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        self.assertIsNone(msg)

    def test_check_daily_limit_enforced(self):
        _ = BarcodeUsage.objects.create(
            barcode=self.barcode, daily_usage_limit=2, total_usage=0
        )
        # No transactions yet
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        # Create two transactions for today
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("Daily usage limit of 2", msg)

    def test_check_total_limit(self):
        # No record allows
        allowed, msg = UsageLimitService.check_total_limit(self.barcode)
        self.assertTrue(allowed)
        # With limit not reached
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode, total_usage_limit=3, total_usage=2
        )
        allowed, msg = UsageLimitService.check_total_limit(self.barcode)
        self.assertTrue(allowed)
        # Reached
        usage.total_usage = 3
        usage.save()
        allowed, msg = UsageLimitService.check_total_limit(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("Total usage limit of 3", msg)

    def test_get_usage_stats_defaults_and_values(self):
        stats = UsageLimitService.get_usage_stats(self.barcode)
        self.assertEqual(stats["daily_used"], 0)
        self.assertEqual(stats["daily_limit"], 0)
        self.assertIsNone(stats["daily_remaining"])
        # Create usage and transactions
        BarcodeUsage.objects.create(
            barcode=self.barcode,
            daily_usage_limit=5,
            total_usage_limit=10,
            total_usage=7,
        )
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        stats = UsageLimitService.get_usage_stats(self.barcode)
        self.assertEqual(stats["daily_used"], 1)
        self.assertEqual(stats["daily_remaining"], 4)
        self.assertEqual(stats["total_used"], 7)
        self.assertEqual(stats["total_remaining"], 3)

    def test_check_daily_limit_boundary_exactly_at_limit(self):
        """Exactly at limit (3 transactions, limit=3) should be blocked."""
        BarcodeUsage.objects.create(
            barcode=self.barcode, daily_usage_limit=3, total_usage=0
        )
        for _ in range(3):
            Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("3", msg)

    def test_check_daily_limit_one_below_limit(self):
        """One below limit (2 transactions, limit=3) should be allowed."""
        BarcodeUsage.objects.create(
            barcode=self.barcode, daily_usage_limit=3, total_usage=0
        )
        for _ in range(2):
            Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        self.assertIsNone(msg)

    def test_check_all_limits_daily_blocks_before_total(self):
        """When daily limit is hit but total is not, daily error is returned."""
        BarcodeUsage.objects.create(
            barcode=self.barcode,
            daily_usage_limit=1,
            total_usage_limit=100,
            total_usage=0,
        )
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        allowed, msg = UsageLimitService.check_all_limits(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("Daily", msg)

    def test_check_all_limits_total_blocks_when_daily_ok(self):
        """When daily is ok but total is hit, total error is returned."""
        BarcodeUsage.objects.create(
            barcode=self.barcode,
            daily_usage_limit=0,  # no daily limit
            total_usage_limit=5,
            total_usage=5,
        )
        allowed, msg = UsageLimitService.check_all_limits(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("Total", msg)

    def test_get_usage_stats_remaining_clamped_to_zero(self):
        """When usage exceeds limit (e.g. limit lowered), remaining should be 0."""
        BarcodeUsage.objects.create(
            barcode=self.barcode,
            daily_usage_limit=2,
            total_usage_limit=3,
            total_usage=10,  # exceeds total limit
        )
        # Create 5 transactions today (exceeds daily limit of 2)
        for _ in range(5):
            Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        stats = UsageLimitService.get_usage_stats(self.barcode)
        self.assertEqual(stats["daily_remaining"], 0)
        self.assertEqual(stats["total_remaining"], 0)


class TransferBarcodeParserTest(TestCase):
    """Unit tests for TransferBarcodeParser"""

    def setUp(self):
        self.parser = TransferBarcodeParser()

    def test_parse_complete_html(self):
        """Test parsing HTML with all fields present"""
        html = """
        <html>
        <h4 class="white-h4" style="margin-top: 10px;">John Doe</h4>
        <h4 id="student-id">12345</h4>
        <img src="data:image/jpeg;base64,dGVzdGltYWdl" />
        <script>
        var formattedTimestamp + "12345678901234"
        </script>
        </html>
        """

        result = self.parser.parse(html)

        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["information_id"], "12345")
        self.assertEqual(result["img_base64"], "dGVzdGltYWdl")
        self.assertEqual(result["barcode"], "12345678901234")

    def test_parse_missing_name(self):
        """Test parsing HTML without name field"""
        html = """
        <html>
        <h4 id="student-id">12345</h4>
        <img src="data:image/jpeg;base64,dGVzdGltYWdl" />
        <script>
        var formattedTimestamp + "12345678901234"
        </script>
        </html>
        """

        result = self.parser.parse(html)

        self.assertIsNone(result["name"])
        self.assertEqual(result["information_id"], "12345")
        self.assertEqual(result["barcode"], "12345678901234")

    def test_parse_missing_student_id(self):
        """Test parsing HTML without student ID field"""
        html = """
        <html>
        <h4 class="white-h4" style="margin-top: 10px;">John Doe</h4>
        <img src="data:image/jpeg;base64,dGVzdGltYWdl" />
        <script>
        var formattedTimestamp + "12345678901234"
        </script>
        </html>
        """

        result = self.parser.parse(html)

        self.assertEqual(result["name"], "John Doe")
        self.assertIsNone(result["information_id"])
        self.assertEqual(result["barcode"], "12345678901234")

    def test_parse_missing_image(self):
        """Test parsing HTML without image field"""
        html = """
        <html>
        <h4 class="white-h4" style="margin-top: 10px;">John Doe</h4>
        <h4 id="student-id">12345</h4>
        <script>
        var formattedTimestamp + "12345678901234"
        </script>
        </html>
        """

        result = self.parser.parse(html)

        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["information_id"], "12345")
        self.assertIsNone(result["img_base64"])
        self.assertEqual(result["barcode"], "12345678901234")

    def test_parse_missing_barcode(self):
        """Test parsing HTML without barcode field"""
        html = """
        <html>
        <h4 class="white-h4" style="margin-top: 10px;">John Doe</h4>
        <h4 id="student-id">12345</h4>
        <img src="data:image/jpeg;base64,dGVzdGltYWdl" />
        </html>
        """

        result = self.parser.parse(html)

        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["information_id"], "12345")
        self.assertEqual(result["img_base64"], "dGVzdGltYWdl")
        self.assertIsNone(result["barcode"])

    def test_parse_empty_html(self):
        """Test parsing empty HTML"""
        html = "<html><body></body></html>"

        result = self.parser.parse(html)

        self.assertIsNone(result["name"])
        self.assertIsNone(result["information_id"])
        self.assertIsNone(result["img_base64"])
        self.assertIsNone(result["barcode"])

    def test_parse_trims_whitespace(self):
        """Test that parsed values have whitespace trimmed"""
        html = (
            '<h4 class="white-h4" style="margin-top: 10px;">  John Doe  </h4>'
            '<h4 id="student-id">  12345  </h4>'
            '<script>formattedTimestamp + "12345678901234"</script>'
        )
        result = self.parser.parse(html)
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["information_id"], "12345")
