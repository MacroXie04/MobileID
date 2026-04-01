"""
DynamoDB configuration for the hybrid database architecture.

Controls DynamoDB connection settings and table naming.
DynamoDB is a required dependency — all barcode, transaction,
user settings, and auth security data is stored there.
"""

import os

# AWS region for DynamoDB
DYNAMODB_REGION = os.getenv("DYNAMODB_REGION", "us-west-2")

# Table name prefix (allows multiple environments to share one AWS account)
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "MobileID-")

# Custom endpoint URL — set to http://localhost:8001 for DynamoDB Local
# Leave empty/unset for production (uses default AWS endpoint)
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL", "") or None

# AWS credentials (optional — prefer IAM roles in production)
# These are only used when explicitly set; boto3 will otherwise use the
# standard credential chain (env vars, ~/.aws/credentials, instance profile).
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "") or None
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "") or None

# Table names (derived from prefix)
DYNAMODB_TABLES = {
    "barcodes": f"{DYNAMODB_TABLE_PREFIX}Barcodes",
    "transactions": f"{DYNAMODB_TABLE_PREFIX}Transactions",
    "user_settings": f"{DYNAMODB_TABLE_PREFIX}UserSettings",
    "auth_security": f"{DYNAMODB_TABLE_PREFIX}AuthSecurity",
}
