"""
Repository for DynamoDB Transactions table operations.

Handles append-only transaction logging with per-user and per-barcode queries.
"""

from __future__ import annotations

import uuid
from typing import Optional

from boto3.dynamodb.conditions import Key
from django.utils import timezone

from core.dynamodb.client import get_table, query_all, query_limited


def _now_iso() -> str:
    return timezone.now().isoformat()


def _table():
    return get_table("transactions")


class TransactionRepository:
    """Data access for the MobileID-Transactions DynamoDB table."""

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        user_id: int,
        barcode_uuid: str = None,
        barcode_value: str = None,
        time_created: str = None,
    ) -> dict:
        """Create a single transaction record."""
        now = time_created or _now_iso()
        txn_id = str(uuid.uuid4())
        sk = f"TXN#{now}#{txn_id}"

        item = {
            "user_id": str(user_id),
            "sk": sk,
            "time_created": now,
        }

        if barcode_uuid:
            item["barcode_uuid"] = str(barcode_uuid)
        if barcode_value:
            item["barcode_value"] = barcode_value

        _table().put_item(Item=item)
        return item

    @staticmethod
    def bulk_create(items: list[dict], batch_size: int = 25) -> list[dict]:
        """
        Batch write transactions. DynamoDB limit is 25 per batch.

        Each item dict should have: user_id, barcode_uuid (optional),
        barcode_value (optional), time_created (optional).
        """
        created = []
        table = _table()

        with table.batch_writer() as batch:
            for item_data in items:
                now = item_data.get("time_created") or _now_iso()
                txn_id = str(uuid.uuid4())
                sk = f"TXN#{now}#{txn_id}"

                item = {
                    "user_id": str(item_data["user_id"]),
                    "sk": sk,
                    "time_created": now,
                }

                barcode_uuid = item_data.get("barcode_uuid")
                if barcode_uuid:
                    item["barcode_uuid"] = str(barcode_uuid)

                barcode_value = item_data.get("barcode_value")
                if barcode_value:
                    item["barcode_value"] = barcode_value

                batch.put_item(Item=item)
                created.append(item)

        return created

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def for_user(
        user_id: int,
        since: str = None,
        until: str = None,
        limit: int = None,
    ) -> list[dict]:
        """
        Query transactions for a user, ordered by time descending.

        SK format is TXN#<iso_time>#<uuid>, so we push time range into
        the KeyConditionExpression for efficient server-side filtering.
        """
        sk_condition = Key("sk").begins_with("TXN#")
        if since and until:
            sk_condition = Key("sk").between(f"TXN#{since}", f"TXN#{until}")
        elif since:
            sk_condition = Key("sk").gte(f"TXN#{since}")
        elif until:
            sk_condition = Key("sk").lte(f"TXN#{until}")

        kwargs = {
            "KeyConditionExpression": Key("user_id").eq(str(user_id)) & sk_condition,
            "ScanIndexForward": False,
        }

        if limit:
            return query_limited(_table(), limit, **kwargs)
        return query_all(_table(), **kwargs)

    @staticmethod
    def for_barcode(
        barcode_uuid: str,
        since: str = None,
        until: str = None,
        limit: int = None,
    ) -> list[dict]:
        """GSI1 query: transactions for a specific barcode."""
        key_expr = Key("barcode_uuid").eq(str(barcode_uuid))
        if since and until:
            key_expr = key_expr & Key("time_created").between(since, until)
        elif since:
            key_expr = key_expr & Key("time_created").gte(since)
        elif until:
            key_expr = key_expr & Key("time_created").lt(until)

        kwargs = {
            "IndexName": "BarcodeTransactionIndex",
            "KeyConditionExpression": key_expr,
            "ScanIndexForward": False,
        }

        if limit:
            return query_limited(_table(), limit, **kwargs)
        return query_all(_table(), **kwargs)

    @staticmethod
    def count_for_barcode_since(barcode_uuid: str, since: str) -> int:
        """
        Count transactions for a barcode since a given time.

        Replaces: Transaction.objects.filter(
            barcode_used=barcode, time_created__gte=start_of_day
        ).count()
        """
        query_kwargs = {
            "IndexName": "BarcodeTransactionIndex",
            "KeyConditionExpression": (
                Key("barcode_uuid").eq(str(barcode_uuid))
                & Key("time_created").gte(since)
            ),
            "Select": "COUNT",
        }
        total = 0
        while True:
            resp = _table().query(**query_kwargs)
            total += resp.get("Count", 0)
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                return total
            query_kwargs["ExclusiveStartKey"] = last_key

    @staticmethod
    def recent_user_barcode_usage(user_id: int, barcode_uuid: str, since: str) -> bool:
        """
        Check if user used a specific barcode recently.

        Replaces: Transaction.objects.filter(
            user=user, barcode_used=barcode, time_created__gte=cutoff
        ).exists()
        """
        from boto3.dynamodb.conditions import Attr

        query_kwargs = {
            "KeyConditionExpression": (
                Key("user_id").eq(str(user_id)) & Key("sk").gte(f"TXN#{since}")
            ),
            "FilterExpression": Attr("barcode_uuid").eq(str(barcode_uuid)),
            "ProjectionExpression": "barcode_uuid",
            "ScanIndexForward": False,
        }
        while True:
            resp = _table().query(**query_kwargs)
            if resp.get("Count", 0) > 0:
                return True
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                return False
            query_kwargs["ExclusiveStartKey"] = last_key

    @staticmethod
    def recent_user_usage(user_id: int, since: str) -> Optional[dict]:
        """
        Get the most recent transaction for a user since a given time.

        Replaces: Transaction.objects.filter(
            user=user, time_created__gte=cutoff
        ).order_by('-time_created').first()
        """
        resp = _table().query(
            KeyConditionExpression=(
                Key("user_id").eq(str(user_id)) & Key("sk").gte(f"TXN#{since}")
            ),
            Limit=1,
            ScanIndexForward=False,
        )
        items = resp.get("Items", [])
        return items[0] if items else None
