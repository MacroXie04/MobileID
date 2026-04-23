"""
Tests for TransferBarcodeParser — regex-driven extraction from transfer HTML.

The parser relies entirely on regex matching, so most failure modes come from
missing fields, whitespace, casing, or format mismatches (e.g. PNG instead of
JPEG). These tests pin the happy path plus each of those failure modes.
"""

from django.test import SimpleTestCase

from index.services.transfer import TransferBarcodeParser


FULL_HTML = """
<div>
  <h4 class="white-h4" style="margin-top:10px;">  Alice Example  </h4>
  <h4 id="student-id"> SID-2024-001 </h4>
  <img src="data:image/jpeg;base64,AAAABBBBCCCCDDDD=="/>
  <script>var foo = formattedTimestamp + "1234567890";</script>
</div>
"""


class TransferBarcodeParserTest(SimpleTestCase):
    def setUp(self):
        self.parser = TransferBarcodeParser()

    def test_parses_complete_html(self):
        result = self.parser.parse(FULL_HTML)
        self.assertEqual(result["name"], "Alice Example")
        self.assertEqual(result["information_id"], "SID-2024-001")
        self.assertEqual(result["img_base64"], "AAAABBBBCCCCDDDD==")
        self.assertEqual(result["barcode"], "1234567890")

    def test_empty_string_returns_all_none(self):
        result = self.parser.parse("")
        self.assertEqual(
            result,
            {
                "name": None,
                "information_id": None,
                "img_base64": None,
                "barcode": None,
            },
        )

    def test_missing_name_returns_none_for_name(self):
        html = FULL_HTML.replace(
            '<h4 class="white-h4" style="margin-top:10px;">  Alice Example  </h4>',
            "",
        )
        result = self.parser.parse(html)
        self.assertIsNone(result["name"])
        self.assertEqual(result["information_id"], "SID-2024-001")

    def test_name_h4_without_margin_top_is_not_matched(self):
        """The `margin-top` marker is required to distinguish the name h4."""
        html = '<h4 class="white-h4">Bob</h4>'
        result = self.parser.parse(html)
        self.assertIsNone(result["name"])

    def test_missing_student_id_returns_none(self):
        html = FULL_HTML.replace(
            '<h4 id="student-id"> SID-2024-001 </h4>',
            "",
        )
        result = self.parser.parse(html)
        self.assertIsNone(result["information_id"])
        self.assertEqual(result["name"], "Alice Example")

    def test_png_image_is_not_matched(self):
        """Only JPEG base64 payloads are extracted, per the regex."""
        html = '<img src="data:image/png;base64,DEADBEEF=="/>'
        result = self.parser.parse(html)
        self.assertIsNone(result["img_base64"])

    def test_missing_magstrip_returns_none_for_barcode(self):
        html = FULL_HTML.replace(
            'formattedTimestamp + "1234567890"',
            'formattedTimestamp + "oops"',  # non-digit suffix, should not match
        )
        result = self.parser.parse(html)
        self.assertIsNone(result["barcode"])

    def test_case_insensitive_matching_for_tags(self):
        html = (
            '<H4 CLASS="white-h4" style="margin-top:5px;">Carol</H4>'
            '<H4 ID="student-id">SID-777</H4>'
            '<IMG SRC="data:image/jpeg;base64,XYZ=="/>'
            'formattedTimestamp + "42"'
        )
        result = self.parser.parse(html)
        self.assertEqual(result["name"], "Carol")
        self.assertEqual(result["information_id"], "SID-777")
        self.assertEqual(result["img_base64"], "XYZ==")
        self.assertEqual(result["barcode"], "42")

    def test_strips_surrounding_whitespace(self):
        html = (
            '<h4 class="white-h4" style="margin-top:1px;">\n   Dave   \n</h4>'
            '<h4 id="student-id">\n  SID-1  \n</h4>'
        )
        result = self.parser.parse(html)
        self.assertEqual(result["name"], "Dave")
        self.assertEqual(result["information_id"], "SID-1")

    def test_returns_first_occurrence_when_multiple_matches(self):
        """Parser uses `search`, which returns the first hit."""
        html = (
            '<h4 class="white-h4" style="margin-top:1px;">First</h4>'
            '<h4 class="white-h4" style="margin-top:1px;">Second</h4>'
        )
        result = self.parser.parse(html)
        self.assertEqual(result["name"], "First")

    def test_magstrip_requires_digits_after_formatted_timestamp(self):
        """Only digit suffixes are captured; extra surrounding quotes handled."""
        html = '  formattedTimestamp    +    "987"  '
        result = self.parser.parse(html)
        self.assertEqual(result["barcode"], "987")
