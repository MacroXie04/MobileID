"""
DynamoDB table creation utility.

Programmatically creates all DynamoDB tables with their GSIs and TTL configuration.
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


def _base_create_kwargs(table_name, key_schema, attribute_definitions):
    kwargs = {
        "TableName": table_name,
        "KeySchema": key_schema,
        "AttributeDefinitions": attribute_definitions,
        "BillingMode": settings.DYNAMODB_BILLING_MODE,
        "TableClass": settings.DYNAMODB_TABLE_CLASS,
    }
    if settings.DYNAMODB_BILLING_MODE != "PAY_PER_REQUEST":
        kwargs["ProvisionedThroughput"] = {
            "ReadCapacityUnits": settings.DYNAMODB_READ_CAPACITY_UNITS,
            "WriteCapacityUnits": settings.DYNAMODB_WRITE_CAPACITY_UNITS,
        }
    return kwargs


def _gsi(index_name, key_schema):
    gsi = {
        "IndexName": index_name,
        "KeySchema": key_schema,
        "Projection": {"ProjectionType": "ALL"},
    }
    if settings.DYNAMODB_BILLING_MODE != "PAY_PER_REQUEST":
        gsi["ProvisionedThroughput"] = {
            "ReadCapacityUnits": settings.DYNAMODB_READ_CAPACITY_UNITS,
            "WriteCapacityUnits": settings.DYNAMODB_WRITE_CAPACITY_UNITS,
        }
    return gsi


def _enable_ttl(table_name, attribute_name):
    resource = get_resource()
    resource.meta.client.update_time_to_live(
        TableName=table_name,
        TimeToLiveSpecification={
            "Enabled": True,
            "AttributeName": attribute_name,
        },
    )


def create_barcodes_table(wait=True):
    """Create the Barcodes table with GSIs."""
    table_name = settings.DYNAMODB_TABLES["barcodes"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "barcode_uuid", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "barcode_uuid", "AttributeType": "S"},
            {"AttributeName": "barcode", "AttributeType": "S"},
            {"AttributeName": "barcode_type", "AttributeType": "S"},
            {"AttributeName": "time_created", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi(
            "BarcodeValueIndex",
            [{"AttributeName": "barcode", "KeyType": "HASH"}],
        ),
        _gsi(
            "SharedBarcodeTypeIndex",
            [
                {"AttributeName": "barcode_type", "KeyType": "HASH"},
                {"AttributeName": "time_created", "KeyType": "RANGE"},
            ],
        ),
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_transactions_table(wait=True):
    """Create the Transactions table with GSI."""
    table_name = settings.DYNAMODB_TABLES["transactions"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "barcode_uuid", "AttributeType": "S"},
            {"AttributeName": "time_created", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi(
            "BarcodeTransactionIndex",
            [
                {"AttributeName": "barcode_uuid", "KeyType": "HASH"},
                {"AttributeName": "time_created", "KeyType": "RANGE"},
            ],
        )
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_user_settings_table(wait=True):
    """Create the UserSettings table (no GSIs)."""
    table_name = settings.DYNAMODB_TABLES["user_settings"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
    )
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_auth_security_table(wait=True):
    """Create the AuthSecurity table with GSI and TTL."""
    table_name = settings.DYNAMODB_TABLES["auth_security"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "entity_type", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi(
            "EntityTypeIndex",
            [
                {"AttributeName": "entity_type", "KeyType": "HASH"},
                {"AttributeName": "created_at", "KeyType": "RANGE"},
            ],
        )
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)

    _enable_ttl(table_name, "expires_at")
    return True


def create_users_table(wait=True):
    """Create the Users table with a username lookup index."""
    table_name = settings.DYNAMODB_TABLES["users"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "username", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi("UsernameIndex", [{"AttributeName": "username", "KeyType": "HASH"}]),
        _gsi("CreatedAtIndex", [{"AttributeName": "created_at", "KeyType": "HASH"}]),
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_user_profiles_table(wait=True):
    """Create the UserProfiles table."""
    table_name = settings.DYNAMODB_TABLES["user_profiles"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "information_id", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi(
            "InformationIdIndex",
            [{"AttributeName": "information_id", "KeyType": "HASH"}],
        )
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_webauthn_credentials_table(wait=True):
    """Create the WebAuthn credentials table."""
    table_name = settings.DYNAMODB_TABLES["webauthn_credentials"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "credential_id", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "credential_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi(
            "CredentialIdIndex",
            [{"AttributeName": "credential_id", "KeyType": "HASH"}],
        ),
        _gsi("CreatedAtIndex", [{"AttributeName": "created_at", "KeyType": "HASH"}]),
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_admin_audit_table(wait=True):
    """Create the AdminAudit table."""
    table_name = settings.DYNAMODB_TABLES["admin_audit"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
            {"AttributeName": "action", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi("ActionIndex", [{"AttributeName": "action", "KeyType": "HASH"}])
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)
    return True


def create_admin_otp_table(wait=True):
    """Create the AdminOtp table with TTL for expiring codes."""
    table_name = settings.DYNAMODB_TABLES["admin_otp"]
    if _table_exists(table_name):
        return False

    resource = get_resource()
    kwargs = _base_create_kwargs(
        table_name=table_name,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "otp_id", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "otp_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
    )
    kwargs["GlobalSecondaryIndexes"] = [
        _gsi("CreatedAtIndex", [{"AttributeName": "created_at", "KeyType": "HASH"}])
    ]
    resource.create_table(**kwargs)
    if wait:
        _wait_for_table(table_name)

    _enable_ttl(table_name, "expires_at")
    return True


def create_all_tables(wait=True):
    """Create all DynamoDB tables. Returns list of created table names."""
    created = []
    for name, fn in [
        ("barcodes", create_barcodes_table),
        ("transactions", create_transactions_table),
        ("user_settings", create_user_settings_table),
        ("auth_security", create_auth_security_table),
        ("users", create_users_table),
        ("user_profiles", create_user_profiles_table),
        ("webauthn_credentials", create_webauthn_credentials_table),
        ("admin_audit", create_admin_audit_table),
        ("admin_otp", create_admin_otp_table),
    ]:
        if fn(wait=wait):
            created.append(settings.DYNAMODB_TABLES[name])
    return created
