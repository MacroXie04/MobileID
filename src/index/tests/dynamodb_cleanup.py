"""
DynamoDB table cleanup utilities for tests.

Since Django's TestCase transaction rollback only works for SQL databases,
DynamoDB data persists across test methods and test classes within the same
test run. This module provides cleanup helpers to ensure test isolation.
"""

from core.dynamodb.client import get_table


def _clear_table(table_key: str) -> None:
    """Delete all items from a DynamoDB table by scanning and batch-deleting."""
    table = get_table(table_key)
    key_schema = table.key_schema
    key_names = [k["AttributeName"] for k in key_schema]

    scan_kwargs = {"ProjectionExpression": ", ".join(key_names)}
    while True:
        resp = table.scan(**scan_kwargs)
        items = resp.get("Items", [])
        if not items:
            break

        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={k: item[k] for k in key_names})

        if not resp.get("LastEvaluatedKey"):
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def clear_all_dynamodb_tables() -> None:
    """Clear all DynamoDB tables."""
    for table_key in ("barcodes", "transactions", "user_settings", "auth_security"):
        _clear_table(table_key)


class DynamoDBCleanupMixin:
    """
    Mixin for Django TestCase classes that use DynamoDB.

    Clears all DynamoDB tables at the start of each test to ensure isolation.
    Must be mixed in with a class that has setUp (Django TestCase).

    Use alongside core.dynamodb.testing.DynamoDBTestMixin (which creates tables
    in setUpClass). This mixin handles per-test data cleanup.
    """

    def setUp(self):
        clear_all_dynamodb_tables()
        super().setUp()
