"""
Repository for DynamoDB AuthSecurity table operations.

Single-table design for 3 entity types:
- AccessTokenBlacklist: PK=JTI#<jti>, SK=BLACKLIST
- FailedLoginAttempt: PK=FAILED#<username>, SK=ATTEMPT
- LoginAuditLog: PK=AUDIT#<username>, SK=LOG#<created_at>#<uuid>
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from boto3.dynamodb.conditions import Attr, Key
from django.utils import timezone

from authn.session_revocation import SESSION_REVOCATION_MATCH_WINDOW_SECONDS
from core.dynamodb.client import get_table, query_limited


def _now_iso() -> str:
    return timezone.now().isoformat()


def _to_epoch(dt: datetime) -> int:
    """Convert datetime to Unix epoch seconds for DynamoDB TTL."""
    return int(dt.timestamp())


def _table():
    return get_table("auth_security")


class SecurityRepository:
    """Data access for the MobileID-AuthSecurity DynamoDB table."""

    # ==================================================================
    # AccessTokenBlacklist operations
    # ==================================================================

    @staticmethod
    def is_blacklisted(jti: str) -> bool:
        """
        Check if an access token JTI is blacklisted.

        Hot path — called on every authenticated request.
        Single GetItem by PK, sub-10ms latency.
        """
        resp = _table().get_item(
            Key={"pk": f"JTI#{jti}", "sk": "BLACKLIST"},
            ProjectionExpression="pk",
        )
        return "Item" in resp

    @staticmethod
    def blacklist_token(jti: str, user_id: int, expires_at: datetime) -> None:
        """
        Add an access token JTI to the blacklist.

        TTL on expires_at ensures automatic cleanup by DynamoDB.
        """
        _table().put_item(
            Item={
                "pk": f"JTI#{jti}",
                "sk": "BLACKLIST",
                "entity_type": "blacklist",
                "jti": jti,
                "user_id": str(user_id),
                "created_at": _now_iso(),
                "expires_at": _to_epoch(expires_at),
            }
        )

    @staticmethod
    def check_session_revocation(
        user_id: int,
        token_iat: int,
        window: int = SESSION_REVOCATION_MATCH_WINDOW_SECONDS,
    ) -> bool:
        """
        Check if a session has been revoked by matching possible session JTIs.

        Uses BatchGetItem to check all ~21 possible JTIs in a single round-trip
        instead of sequential GetItem calls.
        """
        from django.conf import settings
        from core.dynamodb.client import get_resource

        possible_jtis = [
            f"session_{user_id}_{ts}"
            for ts in range(token_iat - window, token_iat + window + 1)
        ]

        table_name = settings.DYNAMODB_TABLES["auth_security"]
        resource = get_resource()

        # Use high-level resource API (simplified key format)
        keys = [{"pk": f"JTI#{jti}", "sk": "BLACKLIST"} for jti in possible_jtis]

        resp = resource.batch_get_item(
            RequestItems={
                table_name: {
                    "Keys": keys,
                    "ProjectionExpression": "pk",
                }
            }
        )

        matched = resp.get("Responses", {}).get(table_name, [])
        return len(matched) > 0

    @staticmethod
    def blacklist_session(user_id: int, session_key: str, expires_at: datetime) -> None:
        """Blacklist a session by its key."""
        SecurityRepository.blacklist_token(session_key, user_id, expires_at)

    # ==================================================================
    # FailedLoginAttempt operations
    # ==================================================================

    @staticmethod
    def get_failed_attempt(username: str) -> Optional[dict]:
        """Get failed login attempt record for a username."""
        resp = _table().get_item(Key={"pk": f"FAILED#{username}", "sk": "ATTEMPT"})
        return resp.get("Item")

    @staticmethod
    def increment_failed_attempt(
        username: str,
        ip_address: str = None,
        max_attempts: int = 5,
        lockout_duration: timedelta = None,
    ) -> dict:
        """
        Atomically increment failed login count. Lock account if threshold reached.

        Returns the updated record.
        """
        now = _now_iso()
        lockout_duration = lockout_duration or timedelta(minutes=30)

        # First, try to increment existing record
        try:
            resp = _table().update_item(
                Key={"pk": f"FAILED#{username}", "sk": "ATTEMPT"},
                UpdateExpression=(
                    "SET attempt_count = attempt_count + :inc, "
                    "last_attempt = :now, ip_address = :ip"
                ),
                ConditionExpression=Attr("pk").exists(),
                ExpressionAttributeValues={
                    ":inc": Decimal("1"),
                    ":now": now,
                    ":ip": ip_address or "",
                },
                ReturnValues="ALL_NEW",
            )
            item = resp.get("Attributes", {})
        except _table().meta.client.exceptions.ConditionalCheckFailedException:
            # Create new record
            item = {
                "pk": f"FAILED#{username}",
                "sk": "ATTEMPT",
                "entity_type": "failed_attempt",
                "username": username,
                "ip_address": ip_address or "",
                "attempt_count": Decimal("1"),
                "last_attempt": now,
                "created_at": now,
            }
            _table().put_item(Item=item)

        # Check if we should lock the account
        count = int(item.get("attempt_count", 0))
        if count >= max_attempts and not item.get("locked_until"):
            locked_until = (timezone.now() + lockout_duration).isoformat()
            _table().update_item(
                Key={"pk": f"FAILED#{username}", "sk": "ATTEMPT"},
                UpdateExpression="SET locked_until = :lu",
                ExpressionAttributeValues={":lu": locked_until},
            )
            item["locked_until"] = locked_until

        return item

    @staticmethod
    def reset_failed_attempts(username: str, ip_address: str = None) -> None:
        """Reset failed attempt counter on successful login."""
        now = _now_iso()
        _table().put_item(
            Item={
                "pk": f"FAILED#{username}",
                "sk": "ATTEMPT",
                "entity_type": "failed_attempt",
                "username": username,
                "ip_address": ip_address or "",
                "attempt_count": Decimal("0"),
                "last_attempt": now,
                "created_at": now,
            }
        )

    @staticmethod
    def is_account_locked(username: str) -> bool:
        """Check if an account is currently locked."""
        item = SecurityRepository.get_failed_attempt(username)
        if not item:
            return False
        locked_until = item.get("locked_until")
        if not locked_until:
            return False
        return locked_until > _now_iso()

    # ==================================================================
    # LoginAuditLog operations
    # ==================================================================

    @staticmethod
    def create_audit_log(
        username: str,
        user_id: int = None,
        ip_address: str = None,
        user_agent: str = None,
        result: str = None,
        reason: str = None,
        success: bool = False,
    ) -> dict:
        """
        Create a login audit log entry.

        Replaces: LoginAuditLog.objects.create(...)
        """
        now = _now_iso()
        log_id = str(uuid.uuid4())

        item = {
            "pk": f"AUDIT#{username}",
            "sk": f"LOG#{now}#{log_id}",
            "entity_type": "audit_log",
            "created_at": now,
            "username": username,
            "success": success,
        }

        if user_id is not None:
            item["user_id"] = str(user_id)
        if ip_address:
            item["ip_address"] = ip_address
        if user_agent:
            item["user_agent"] = user_agent
        if result:
            item["result"] = result
        if reason:
            item["reason"] = reason

        _table().put_item(Item=item)
        return item

    @staticmethod
    def get_audit_logs_for_user(
        username: str, limit: int = 50, since: str = None
    ) -> list[dict]:
        """Get login audit logs for a username, most recent first."""
        if since:
            key_expr = Key("pk").eq(f"AUDIT#{username}") & Key("sk").gte(f"LOG#{since}")
        else:
            key_expr = Key("pk").eq(f"AUDIT#{username}") & Key("sk").begins_with("LOG#")

        return query_limited(
            _table(),
            limit,
            KeyConditionExpression=key_expr,
            ScanIndexForward=False,
        )
