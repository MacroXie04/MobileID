"""
DynamoDB test utilities using moto to mock AWS services.

The DynamoDBTestRunner (core.test_runner) starts a global moto mock and
creates all tables for the entire test run.  This mixin is only needed
when running individual test classes outside the custom runner.

Usage:
    from core.dynamodb.testing import DynamoDBTestMixin

    class MyTest(DynamoDBTestMixin, TestCase):
        def test_something(self):
            # DynamoDB tables are created and available
            ...
"""

import os

# Force moto to intercept boto3 calls
os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")


class DynamoDBTestMixin:
    """
    Mixin that ensures moto-mocked DynamoDB tables exist.

    If a global moto mock is already active (e.g. via DynamoDBTestRunner),
    this mixin is a no-op.  Otherwise it starts its own moto context.
    """

    _owns_mock = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        from moto import mock_aws
        from core.dynamodb.client import reset

        # Detect whether a moto mock is already active
        try:
            from core.dynamodb.tables import _table_exists
            from django.conf import settings
            table_name = settings.DYNAMODB_TABLES["barcodes"]
            _table_exists(table_name)
            cls._owns_mock = False
        except Exception:
            cls._mock_aws = mock_aws()
            cls._mock_aws.start()
            cls._owns_mock = True
            reset()

            from core.dynamodb.tables import create_all_tables
            create_all_tables(wait=True)

    @classmethod
    def tearDownClass(cls):
        if cls._owns_mock:
            cls._mock_aws.stop()
            from core.dynamodb.client import reset
            reset()

        super().tearDownClass()
