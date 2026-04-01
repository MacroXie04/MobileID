"""
Repository for DynamoDB Barcodes table operations.

Encapsulates all DynamoDB access for barcode items, including
denormalized profile and usage data.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from boto3.dynamodb.conditions import Attr, Key
from django.utils import timezone

from core.dynamodb.client import get_table, query_all


def _now_iso() -> str:
    return timezone.now().isoformat()


def _table():
    return get_table("barcodes")


class BarcodeRepository:
    """Data access for the MobileID-Barcodes DynamoDB table."""

    # ------------------------------------------------------------------
    # Single-item reads
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_uuid(user_id: int, barcode_uuid: str) -> Optional[dict]:
        """Get a barcode item by user_id + barcode_uuid."""
        resp = _table().get_item(
            Key={"user_id": str(user_id), "barcode_uuid": str(barcode_uuid)}
        )
        return resp.get("Item")

    @staticmethod
    def get_by_barcode_value(barcode_value: str) -> Optional[dict]:
        """GSI1 lookup — find barcode by its unique value."""
        resp = _table().query(
            IndexName="BarcodeValueIndex",
            KeyConditionExpression=Key("barcode").eq(barcode_value),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    @staticmethod
    def barcode_exists(barcode_value: str) -> bool:
        """Check if a barcode value exists (GSI1, projection to keys only)."""
        resp = _table().query(
            IndexName="BarcodeValueIndex",
            KeyConditionExpression=Key("barcode").eq(barcode_value),
            Select="COUNT",
            Limit=1,
        )
        return resp.get("Count", 0) > 0

    # ------------------------------------------------------------------
    # Multi-item reads
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_barcodes(user_id: int) -> list[dict]:
        """Get all barcodes owned by a user, ordered by time_created desc."""
        items = query_all(
            _table(),
            KeyConditionExpression=Key("user_id").eq(str(user_id)),
            ScanIndexForward=False,
        )
        items.sort(key=lambda x: x.get("time_created", ""), reverse=True)
        return items

    @staticmethod
    def get_user_barcodes_by_type(user_id: int, barcode_type: str) -> list[dict]:
        """Get all barcodes of a specific type for a user."""
        return query_all(
            _table(),
            KeyConditionExpression=Key("user_id").eq(str(user_id)),
            FilterExpression=Attr("barcode_type").eq(barcode_type),
        )

    @staticmethod
    def get_shared_dynamic_barcodes(exclude_user_id: int = None) -> list[dict]:
        """GSI2 query: shared DynamicBarcodes for pull pool / dashboard."""
        items = query_all(
            _table(),
            IndexName="SharedBarcodeTypeIndex",
            KeyConditionExpression=Key("barcode_type").eq("DynamicBarcode"),
            FilterExpression=Attr("share_with_others").eq(True),
            ScanIndexForward=False,
        )
        if exclude_user_id is not None:
            items = [i for i in items if i.get("user_id") != str(exclude_user_id)]
        return items

    @staticmethod
    def get_dashboard_barcodes(user_id: int) -> list[dict]:
        """
        Composite query replacing the complex Q() filter in retrieve.py.

        Returns user's own barcodes + shared DynamicBarcodes from other users,
        sorted by time_created descending.
        """
        user_id_str = str(user_id)

        # Query 1: All user's own barcodes
        own = query_all(
            _table(),
            KeyConditionExpression=Key("user_id").eq(user_id_str),
        )

        # Query 2: Shared DynamicBarcodes (may include user's own)
        shared = query_all(
            _table(),
            IndexName="SharedBarcodeTypeIndex",
            KeyConditionExpression=Key("barcode_type").eq("DynamicBarcode"),
            FilterExpression=Attr("share_with_others").eq(True),
            ScanIndexForward=False,
        )

        # Merge and deduplicate (user's own DynamicBarcodes may appear in both)
        seen = set()
        merged = []
        for item in own + shared:
            key = (item["user_id"], item["barcode_uuid"])
            if key not in seen:
                seen.add(key)
                merged.append(item)

        # Sort by time_created descending
        merged.sort(key=lambda x: x.get("time_created", ""), reverse=True)
        return merged

    @staticmethod
    def get_pull_candidates(
        gender_setting: str,
        exclude_user_id: int,
        cooldown_cutoff: str,
    ) -> list[dict]:
        """
        Get barcode candidates for the pull pool.

        Returns shared DynamicBarcodes matching gender from other users,
        excluding recently used ones (cooldown filter).
        """
        # Get all shared DynamicBarcodes
        all_shared = query_all(
            _table(),
            IndexName="SharedBarcodeTypeIndex",
            KeyConditionExpression=Key("barcode_type").eq("DynamicBarcode"),
            FilterExpression=Attr("share_with_others").eq(True),
            ScanIndexForward=False,
        )

        exclude_str = str(exclude_user_id)
        candidates = []
        for item in all_shared:
            # Exclude the requesting user's own barcodes
            if item.get("user_id") == exclude_str:
                continue

            # Gender filter
            if item.get("profile_gender") != gender_setting:
                continue

            # Usage cooldown filter
            last_used = item.get("last_used")
            if last_used and last_used >= cooldown_cutoff:
                continue

            candidates.append(item)

        return candidates

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        user_id: int,
        barcode_value: str,
        barcode_type: str = "Others",
        barcode_uuid: str = None,
        owner_username: str = None,
        share_with_others: bool = False,
        profile_name: str = None,
        profile_info_id: str = None,
        profile_avatar: str = None,
        profile_gender: str = None,
        time_created: str = None,
    ) -> dict:
        """
        Create a new barcode item.

        Callers must check barcode_exists() beforehand to enforce value
        uniqueness — DynamoDB GSIs do not enforce unique constraints.
        A ConditionExpression on the primary key prevents duplicate items
        for the same (user_id, barcode_uuid) pair.
        """
        bc_uuid = barcode_uuid or str(uuid.uuid4())
        now = time_created or _now_iso()

        item = {
            "user_id": str(user_id),
            "barcode_uuid": bc_uuid,
            "barcode": barcode_value,
            "barcode_type": barcode_type,
            "share_with_others": share_with_others,
            "time_created": now,
            "total_usage": 0,
            "total_usage_limit": 0,
            "daily_usage_limit": 0,
        }

        if owner_username:
            item["owner_username"] = owner_username
        if profile_name:
            item["profile_name"] = profile_name
        if profile_info_id:
            item["profile_info_id"] = profile_info_id
        if profile_avatar:
            item["profile_avatar"] = profile_avatar
        if profile_gender:
            item["profile_gender"] = profile_gender

        _table().put_item(
            Item=item,
            ConditionExpression=Attr("user_id").not_exists(),
        )
        return item

    @staticmethod
    def update(user_id: int, barcode_uuid: str, **updates) -> dict:
        """Partial update via UpdateExpression."""
        expr_parts = []
        expr_names = {}
        expr_values = {}

        for i, (key, value) in enumerate(updates.items()):
            alias = f"#k{i}"
            val_alias = f":v{i}"
            expr_parts.append(f"{alias} = {val_alias}")
            expr_names[alias] = key
            expr_values[val_alias] = value

        if not expr_parts:
            return {}

        resp = _table().update_item(
            Key={"user_id": str(user_id), "barcode_uuid": str(barcode_uuid)},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        return resp.get("Attributes", {})

    @staticmethod
    def delete(user_id: int, barcode_uuid: str) -> bool:
        """Delete a barcode item."""
        _table().delete_item(
            Key={"user_id": str(user_id), "barcode_uuid": str(barcode_uuid)}
        )
        return True

    @staticmethod
    def increment_usage(user_id: int, barcode_uuid: str) -> None:
        """
        Atomic counter: total_usage += 1, last_used = now.

        Replaces F('total_usage') + 1 from Django ORM.
        """
        _table().update_item(
            Key={"user_id": str(user_id), "barcode_uuid": str(barcode_uuid)},
            UpdateExpression="SET total_usage = total_usage + :inc, last_used = :now",
            ExpressionAttributeValues={
                ":inc": Decimal("1"),
                ":now": _now_iso(),
            },
        )
