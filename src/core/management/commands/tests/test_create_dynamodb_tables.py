"""Tests for the create_dynamodb_tables management command.

The custom test runner (core.test_runner.DynamoDBTestRunner) has already
started moto and created all tables once at test-suite setup. These tests
exercise the command itself, primarily along the idempotent path and with
tables selectively deleted so that the creation branch also runs.
"""

from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from core.dynamodb.client import get_client, get_resource


class CreateDynamoDBTablesCommandTest(TestCase):
    def _run(self, *args):
        out = StringIO()
        call_command("create_dynamodb_tables", *args, stdout=out)
        return out.getvalue()

    def test_reports_all_tables_already_exist_on_second_run(self):
        # Runner has already created everything once. A fresh invocation
        # should find every table present and skip creation.
        output = self._run()

        self.assertIn("All tables already exist.", output)
        self.assertIn(f"Region: {settings.DYNAMODB_REGION}", output)
        self.assertIn(f"Table prefix: {settings.DYNAMODB_TABLE_PREFIX}", output)

    def test_is_idempotent_when_run_repeatedly(self):
        self._run()
        output = self._run()

        self.assertIn("All tables already exist.", output)

    def test_recreates_missing_tables(self):
        # Delete one table and verify the command re-creates it rather than
        # erroring out and that the creation is reported.
        client = get_client()
        barcode_table_name = settings.DYNAMODB_TABLES["barcodes"]

        client.delete_table(TableName=barcode_table_name)
        waiter = client.get_waiter("table_not_exists")
        waiter.wait(TableName=barcode_table_name)

        output = self._run("--no-wait")

        self.assertIn(f"Created: {barcode_table_name}", output)
        # Table should now exist again — load() will raise if it does not.
        get_resource().Table(barcode_table_name).load()

    def test_honors_no_wait_flag_without_error(self):
        # Idempotent path + --no-wait — should still succeed and not block
        # on any waiter since no new tables are created.
        output = self._run("--no-wait")

        self.assertIn("All tables already exist.", output)
