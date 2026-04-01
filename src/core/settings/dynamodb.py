"""
DynamoDB configuration for the hybrid database architecture.

Controls DynamoDB connection settings and table naming.
DynamoDB is a required dependency — all barcode, transaction,
user settings, and auth security data is stored there.
"""

import os

# Primary persistence mode.
# "hybrid" keeps the existing SQL + DynamoDB architecture.
# "dynamodb" is the production target for the low-cost AWS deployment.
PERSISTENCE_MODE = os.getenv("PERSISTENCE_MODE", "hybrid").lower()

# AWS region for DynamoDB
DYNAMODB_REGION = os.getenv("DYNAMODB_REGION", "us-west-2")

# Table name prefix (allows multiple environments to share one AWS account)
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "MobileID-")

# Cost-first defaults for production deployments.
DYNAMODB_BILLING_MODE = os.getenv("DYNAMODB_BILLING_MODE", "PAY_PER_REQUEST").upper()
DYNAMODB_TABLE_CLASS = os.getenv("DYNAMODB_TABLE_CLASS", "STANDARD").upper()
DYNAMODB_READ_CAPACITY_UNITS = int(os.getenv("DYNAMODB_READ_CAPACITY_UNITS", "5"))
DYNAMODB_WRITE_CAPACITY_UNITS = int(os.getenv("DYNAMODB_WRITE_CAPACITY_UNITS", "5"))

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
    "users": f"{DYNAMODB_TABLE_PREFIX}Users",
    "user_profiles": f"{DYNAMODB_TABLE_PREFIX}UserProfiles",
    "webauthn_credentials": f"{DYNAMODB_TABLE_PREFIX}WebAuthnCredentials",
    "admin_audit": f"{DYNAMODB_TABLE_PREFIX}AdminAudit",
    "admin_otp": f"{DYNAMODB_TABLE_PREFIX}AdminOtp",
}

if PERSISTENCE_MODE == "dynamodb":
    DYNAMODB_REQUIRED_TABLE_KEYS = tuple(DYNAMODB_TABLES.keys())
else:
    DYNAMODB_REQUIRED_TABLE_KEYS = (
        "barcodes",
        "transactions",
        "user_settings",
        "auth_security",
    )
