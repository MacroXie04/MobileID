"""
Repository for DynamoDB UserSettings table operations.

Merges UserBarcodeSettings + UserBarcodePullSettings + BarcodePullSettings
into a single DynamoDB item per user.
"""

from __future__ import annotations

from typing import Optional

from boto3.dynamodb.conditions import Attr
from core.dynamodb.client import get_table

# Default values matching Django model defaults
_DEFAULTS = {
    "sk": "SETTINGS",
    "active_barcode_uuid": None,
    "associate_user_profile_with_barcode": False,
    "scanner_detection_enabled": False,
    "prefer_front_camera": True,
    "pull_setting": "Disable",
    "pull_gender_setting": "Unknow",
    "barcode_pull_gender_setting": "Unknow",
    "active_barcode_owner_id": None,
}


def _table():
    return get_table("user_settings")


class SettingsRepository:
    """Data access for the MobileID-UserSettings DynamoDB table."""

    @staticmethod
    def get(user_id: int) -> Optional[dict]:
        """Get user settings. Returns None if not found."""
        resp = _table().get_item(Key={"user_id": str(user_id), "sk": "SETTINGS"})
        return resp.get("Item")

    @staticmethod
    def get_or_create(user_id: int) -> dict:
        """
        Get user settings, creating with defaults if they don't exist.

        Replaces: UserBarcodeSettings.objects.get_or_create(user=user, defaults={...})
        """
        item = SettingsRepository.get(user_id)
        if item:
            return item

        # Create with defaults
        item = {"user_id": str(user_id), **_DEFAULTS}
        _table().put_item(
            Item={k: v for k, v in item.items() if v is not None},
            ConditionExpression=Attr("user_id").not_exists(),
        )
        return item

    @staticmethod
    def update(user_id: int, **updates) -> dict:
        """
        Update specific settings fields.

        Returns the full updated item.
        """
        if not updates:
            return SettingsRepository.get_or_create(user_id)

        expr_parts = []
        expr_names = {}
        expr_values = {}
        remove_parts = []

        for i, (key, value) in enumerate(updates.items()):
            alias = f"#k{i}"
            expr_names[alias] = key
            if value is None:
                remove_parts.append(alias)
            else:
                val_alias = f":v{i}"
                expr_parts.append(f"{alias} = {val_alias}")
                expr_values[val_alias] = value

        update_expr = ""
        if expr_parts:
            update_expr += "SET " + ", ".join(expr_parts)
        if remove_parts:
            if update_expr:
                update_expr += " "
            update_expr += "REMOVE " + ", ".join(remove_parts)

        kwargs = {
            "Key": {"user_id": str(user_id), "sk": "SETTINGS"},
            "UpdateExpression": update_expr,
            "ReturnValues": "ALL_NEW",
        }
        if expr_names:
            kwargs["ExpressionAttributeNames"] = expr_names
        if expr_values:
            kwargs["ExpressionAttributeValues"] = expr_values

        resp = _table().update_item(**kwargs)
        return resp.get("Attributes", {})

    @staticmethod
    def set_active_barcode(
        user_id: int, barcode_uuid: str = None, owner_user_id: int | str = None
    ) -> dict:
        """Set or clear the active barcode."""
        if barcode_uuid:
            updates = {"active_barcode_uuid": str(barcode_uuid)}
            if owner_user_id is not None:
                updates["active_barcode_owner_id"] = str(owner_user_id)
            else:
                updates["active_barcode_owner_id"] = str(user_id)
            return SettingsRepository.update(user_id, **updates)
        return SettingsRepository.update(
            user_id, active_barcode_uuid=None, active_barcode_owner_id=None
        )

    @staticmethod
    def get_active_barcode(user_id: int, settings: dict) -> Optional[dict]:
        """Resolve the active barcode using stored owner metadata when present."""
        from index.repositories.barcode_repo import (
            DASHBOARD_SHARED_BARCODE_LIMIT,
            SHARED_DYNAMIC_QUERY_PAGE_SIZE,
            BarcodeRepository,
        )

        barcode_uuid = settings.get("active_barcode_uuid")
        if not barcode_uuid:
            return None

        owner_id = settings.get("active_barcode_owner_id") or user_id
        barcode = BarcodeRepository.get_by_uuid(owner_id, barcode_uuid)
        if barcode:
            return barcode

        if settings.get("active_barcode_owner_id"):
            return None

        # Legacy settings may only contain the UUID. Search a bounded slice of
        # the shared pool as a compatibility fallback, then persist owner context
        # if the active shared barcode is found.
        for shared in BarcodeRepository.get_shared_dynamic_barcodes(
            limit=DASHBOARD_SHARED_BARCODE_LIMIT,
            page_size=SHARED_DYNAMIC_QUERY_PAGE_SIZE,
        ):
            if shared.get("barcode_uuid") == barcode_uuid:
                SettingsRepository.set_active_barcode(
                    user_id,
                    barcode_uuid,
                    owner_user_id=shared.get("user_id"),
                )
                return shared
        return None

    @staticmethod
    def set_active_barcode_owner(
        user_id: int, barcode_uuid: str, owner_user_id
    ) -> dict:
        """Backfill active barcode owner metadata after validation."""
        if not barcode_uuid:
            return SettingsRepository.set_active_barcode(user_id, None)
        return SettingsRepository.update(
            user_id,
            active_barcode_uuid=str(barcode_uuid),
            active_barcode_owner_id=str(owner_user_id),
        )

    @staticmethod
    def set_active_own_barcode(user_id: int, barcode_uuid: str = None) -> dict:
        """Set an active barcode owned by the same user."""
        if barcode_uuid:
            return SettingsRepository.update(
                user_id,
                active_barcode_uuid=str(barcode_uuid),
                active_barcode_owner_id=str(user_id),
            )
        return SettingsRepository.set_active_barcode(user_id, None)

    @staticmethod
    def clear_barcode_if_matches(user_id: int, barcode_uuid: str) -> bool:
        """
        Clear active_barcode_uuid only if it matches the given UUID.

        Returns True if cleared, False if it didn't match.
        Replaces: UserBarcodeSettings.objects.filter(
            barcode=barcode
        ).update(barcode=None)
        """
        try:
            _table().update_item(
                Key={"user_id": str(user_id), "sk": "SETTINGS"},
                UpdateExpression="REMOVE #abc, #owner",
                ConditionExpression=Attr("active_barcode_uuid").eq(str(barcode_uuid)),
                ExpressionAttributeNames={
                    "#abc": "active_barcode_uuid",
                    "#owner": "active_barcode_owner_id",
                },
            )
            return True
        except _table().meta.client.exceptions.ConditionalCheckFailedException:
            return False
