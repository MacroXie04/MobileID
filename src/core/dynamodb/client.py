"""
Shared DynamoDB client and resource helpers.

Provides a singleton boto3 resource for connection reuse across the application.
"""

import boto3
from botocore.config import Config
from django.conf import settings

_resource = None
_client = None


def _build_kwargs():
    """Build common boto3 kwargs from Django settings."""
    kwargs = {
        "region_name": settings.DYNAMODB_REGION,
        "config": Config(
            connect_timeout=settings.DYNAMODB_CONNECT_TIMEOUT_SECONDS,
            read_timeout=settings.DYNAMODB_READ_TIMEOUT_SECONDS,
            retries={
                "max_attempts": settings.DYNAMODB_MAX_ATTEMPTS,
                "mode": "standard",
            },
        ),
    }
    if settings.DYNAMODB_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return kwargs


def get_resource():
    """Return a singleton boto3 DynamoDB resource."""
    global _resource
    if _resource is None:
        _resource = boto3.resource("dynamodb", **_build_kwargs())
    return _resource


def get_client():
    """Return a singleton boto3 DynamoDB client (low-level)."""
    global _client
    if _client is None:
        _client = boto3.client("dynamodb", **_build_kwargs())
    return _client


def get_table(name_key):
    """
    Get a DynamoDB Table object by its settings key.

    Args:
        name_key: One of 'barcodes', 'transactions', 'user_settings', 'auth_security'

    Returns:
        boto3 Table resource
    """
    table_name = settings.DYNAMODB_TABLES[name_key]
    return get_resource().Table(table_name)


def query_all(table, **kwargs):
    """
    Auto-paginating query that follows LastEvaluatedKey.

    Returns a flat list of all matching items across all pages.
    """
    items = []
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        kwargs["ExclusiveStartKey"] = last_key
    return items


def query_limited(table, max_items, **kwargs):
    """
    Paginating query that stops once max_items items have been collected.

    Sets per-page Limit as an optimization hint (unless the caller passed
    a smaller Limit). With FilterExpression, Limit bounds pre-filter rows,
    so callers using filters may want to pass a larger per-page Limit.
    """
    if max_items <= 0:
        raise ValueError("max_items must be positive")

    per_page = kwargs.get("Limit")
    if per_page is None or per_page > max_items:
        kwargs["Limit"] = max_items

    items = []
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        if len(items) >= max_items:
            return items[:max_items]
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        kwargs["ExclusiveStartKey"] = last_key
    return items


def reset():
    """Reset cached clients (useful for testing)."""
    global _resource, _client
    _resource = None
    _client = None
