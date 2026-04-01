"""
DynamoDB table creation utility.

Programmatically creates all 4 tables with their GSIs and TTL configuration.
Idempotent — skips tables that already exist.
"""

from django.conf import settings

from core.dynamodb.client import get_resource


def _table_exists(table_name):
    """Check if a DynamoDB table already exists."""
    resource = get_resource()
    try:
        table = resource.Table(table_name)
        table.load()
        return True
    except resource.meta.client.exceptions.ResourceNotFoundException:
        return False


def _wait_for_table(table_name):
    """Wait until a table becomes ACTIVE."""
    resource = get_resource()
    table = resource.Table(table_name)
    table.wait_until_exists()


def create_barcodes_table(wait=True):
    """Create the Barcodes table with GSIs."""
    table_name = settings.DYNAMODB_TABLES["barcodes"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "barcode_uuid", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "barcode_uuid", "AttributeType": "S"},
            {"AttributeName": "barcode", "AttributeType": "S"},
            {"AttributeName": "barcode_type", "AttributeType": "S"},
            {"AttributeName": "time_created", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "BarcodeValueIndex",
                "KeySchema": [
                    {"AttributeName": "barcode", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
            {
                "IndexName": "SharedBarcodeTypeIndex",
                "KeySchema": [
                    {"AttributeName": "barcode_type", "KeyType": "HASH"},
                    {"AttributeName": "time_created", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    if wait:
        _wait_for_table(table_name)
    return True


def create_transactions_table(wait=True):
    """Create the Transactions table with GSI."""
    table_name = settings.DYNAMODB_TABLES["transactions"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "barcode_uuid", "AttributeType": "S"},
            {"AttributeName": "time_created", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "BarcodeTransactionIndex",
                "KeySchema": [
                    {"AttributeName": "barcode_uuid", "KeyType": "HASH"},
                    {"AttributeName": "time_created", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    if wait:
        _wait_for_table(table_name)
    return True


def create_user_settings_table(wait=True):
    """Create the UserSettings table (no GSIs)."""
    table_name = settings.DYNAMODB_TABLES["user_settings"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    if wait:
        _wait_for_table(table_name)
    return True


def create_auth_security_table(wait=True):
    """Create the AuthSecurity table with GSI and TTL."""
    table_name = settings.DYNAMODB_TABLES["auth_security"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "entity_type", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "EntityTypeIndex",
                "KeySchema": [
                    {"AttributeName": "entity_type", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    if wait:
        _wait_for_table(table_name)

    # Enable TTL on expires_at attribute
    client = resource.meta.client
    client.update_time_to_live(
        TableName=table_name,
        TimeToLiveSpecification={
            "Enabled": True,
            "AttributeName": "expires_at",
        },
    )
    return True


def create_all_tables(wait=True):
    """Create all DynamoDB tables. Returns list of created table names."""
    created = []
    for name, fn in [
        ("barcodes", create_barcodes_table),
        ("transactions", create_transactions_table),
        ("user_settings", create_user_settings_table),
        ("auth_security", create_auth_security_table),
    ]:
        if fn(wait=wait):
            created.append(settings.DYNAMODB_TABLES[name])
    return created
