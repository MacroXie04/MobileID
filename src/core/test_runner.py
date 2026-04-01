"""
Custom Django test runner that sets up moto-mocked DynamoDB for all tests.
"""

from django.test.runner import DiscoverRunner


class DynamoDBTestRunner(DiscoverRunner):
    """Test runner that wraps all tests with moto DynamoDB mocking."""

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)

        import os

        os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-2")
        os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")

        from moto import mock_aws

        self._mock_aws = mock_aws()
        self._mock_aws.start()

        # Reset client cache so connections go through moto
        from core.dynamodb.client import reset

        reset()

        # Create all DynamoDB tables
        from core.dynamodb.tables import create_all_tables

        create_all_tables(wait=True)

    def teardown_test_environment(self, **kwargs):
        self._mock_aws.stop()

        from core.dynamodb.client import reset

        reset()

        super().teardown_test_environment(**kwargs)
