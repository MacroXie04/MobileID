"""Tests for core.dynamodb.client singleton helpers and query_all pagination."""

from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings

from core.dynamodb import client as client_mod


class BuildKwargsTest(TestCase):
    @override_settings(
        DYNAMODB_REGION="us-west-2",
        DYNAMODB_ENDPOINT_URL="http://localhost:8001",
        AWS_ACCESS_KEY_ID="ak",
        AWS_SECRET_ACCESS_KEY="sk",
    )
    def test_includes_all_fields_when_set(self):
        kwargs = client_mod._build_kwargs()

        self.assertEqual(kwargs["region_name"], "us-west-2")
        self.assertEqual(kwargs["endpoint_url"], "http://localhost:8001")
        self.assertEqual(kwargs["aws_access_key_id"], "ak")
        self.assertEqual(kwargs["aws_secret_access_key"], "sk")

    @override_settings(
        DYNAMODB_REGION="us-east-1",
        DYNAMODB_ENDPOINT_URL="",
        AWS_ACCESS_KEY_ID="",
        AWS_SECRET_ACCESS_KEY="",
    )
    def test_omits_optional_fields_when_empty(self):
        kwargs = client_mod._build_kwargs()

        self.assertEqual(kwargs, {"region_name": "us-east-1"})

    @override_settings(
        DYNAMODB_REGION="us-east-1",
        DYNAMODB_ENDPOINT_URL="http://localhost:8001",
        AWS_ACCESS_KEY_ID="ak",
        AWS_SECRET_ACCESS_KEY="",  # partial creds → both omitted
    )
    def test_omits_creds_when_either_key_missing(self):
        kwargs = client_mod._build_kwargs()

        self.assertNotIn("aws_access_key_id", kwargs)
        self.assertNotIn("aws_secret_access_key", kwargs)
        self.assertEqual(kwargs["endpoint_url"], "http://localhost:8001")


class SingletonCacheTest(TestCase):
    def tearDown(self):
        # Restore the test-runner's shared moto-backed resource/client.
        client_mod.reset()

    def test_get_resource_returns_same_instance(self):
        client_mod.reset()
        first = client_mod.get_resource()
        second = client_mod.get_resource()

        self.assertIs(first, second)

    def test_get_client_returns_same_instance(self):
        client_mod.reset()
        first = client_mod.get_client()
        second = client_mod.get_client()

        self.assertIs(first, second)

    def test_reset_clears_both_caches(self):
        first_resource = client_mod.get_resource()
        first_client = client_mod.get_client()

        client_mod.reset()

        self.assertIsNot(client_mod.get_resource(), first_resource)
        self.assertIsNot(client_mod.get_client(), first_client)


class GetTableTest(TestCase):
    def test_returns_table_named_after_settings_entry(self):
        table = client_mod.get_table("barcodes")

        self.assertEqual(table.name, settings.DYNAMODB_TABLES["barcodes"])

    def test_raises_keyerror_for_unknown_key(self):
        with self.assertRaises(KeyError):
            client_mod.get_table("does-not-exist")


class QueryAllTest(TestCase):
    def test_collects_all_items_across_pages(self):
        fake_table = MagicMock()
        fake_table.query.side_effect = [
            {"Items": [{"id": 1}, {"id": 2}], "LastEvaluatedKey": {"id": 2}},
            {"Items": [{"id": 3}]},
        ]

        items = client_mod.query_all(fake_table, KeyConditionExpression="placeholder")

        self.assertEqual(items, [{"id": 1}, {"id": 2}, {"id": 3}])
        self.assertEqual(fake_table.query.call_count, 2)

        second_call_kwargs = fake_table.query.call_args_list[1].kwargs
        self.assertEqual(second_call_kwargs["ExclusiveStartKey"], {"id": 2})

    def test_returns_empty_list_when_no_items(self):
        fake_table = MagicMock()
        fake_table.query.return_value = {"Items": []}

        items = client_mod.query_all(fake_table, KeyConditionExpression="x")

        self.assertEqual(items, [])
        fake_table.query.assert_called_once()

    def test_stops_when_no_last_evaluated_key(self):
        fake_table = MagicMock()
        fake_table.query.return_value = {"Items": [{"id": 1}]}

        items = client_mod.query_all(fake_table)

        self.assertEqual(items, [{"id": 1}])
        fake_table.query.assert_called_once()

    def test_passes_kwargs_through_to_table_query(self):
        fake_table = MagicMock()
        fake_table.query.return_value = {"Items": []}

        client_mod.query_all(
            fake_table,
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": "abc"},
        )

        kwargs = fake_table.query.call_args.kwargs
        self.assertEqual(kwargs["KeyConditionExpression"], "pk = :pk")
        self.assertEqual(kwargs["ExpressionAttributeValues"], {":pk": "abc"})


class BotoConstructionTest(TestCase):
    """Verify the cached path actually invokes boto3 when cache is empty."""

    def tearDown(self):
        client_mod.reset()

    def test_get_resource_calls_boto3_with_build_kwargs(self):
        client_mod.reset()
        sentinel = MagicMock(name="resource")
        with patch("core.dynamodb.client.boto3") as mock_boto3:
            mock_boto3.resource.return_value = sentinel
            result = client_mod.get_resource()

        self.assertIs(result, sentinel)
        mock_boto3.resource.assert_called_once()
        call_args = mock_boto3.resource.call_args
        self.assertEqual(call_args.args, ("dynamodb",))

    def test_get_client_calls_boto3_with_build_kwargs(self):
        client_mod.reset()
        sentinel = MagicMock(name="client")
        with patch("core.dynamodb.client.boto3") as mock_boto3:
            mock_boto3.client.return_value = sentinel
            result = client_mod.get_client()

        self.assertIs(result, sentinel)
        mock_boto3.client.assert_called_once()
