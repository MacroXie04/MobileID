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
    def set_active_barcode(user_id: int, barcode_uuid: str = None) -> dict:
        """Set or clear the active barcode."""
        if barcode_uuid:
            return SettingsRepository.update(
                user_id, active_barcode_uuid=str(barcode_uuid)
            )
        return SettingsRepository.update(user_id, active_barcode_uuid=None)

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
                UpdateExpression="REMOVE #abc",
                ConditionExpression=Attr("active_barcode_uuid").eq(str(barcode_uuid)),
                ExpressionAttributeNames={"#abc": "active_barcode_uuid"},
            )
            return True
        except _table().meta.client.exceptions.ConditionalCheckFailedException:
            return False
