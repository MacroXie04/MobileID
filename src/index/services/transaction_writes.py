from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Sequence, Dict, Any

from django.contrib.auth.models import User
from django.utils import timezone

from index.repositories import TransactionRepository


@dataclass(frozen=True)
class CreatedTransaction:
    """Lightweight return type for bulk_create summaries."""

    txn_id: str
    user_id: int
    barcode_uuid: Optional[str]
    time_created: str


class TransactionWriteMixin:
    """Write operations for Transaction service."""

    @staticmethod
    def create_transaction(
        *,
        user: User,
        barcode: object = None,
        time_created: Optional[datetime] = None,
        save: bool = True,
    ) -> dict:
        """
        Create and persist a Transaction in DynamoDB.

        Accepts either a Django Barcode model or a dict from DynamoDB.
        """
        if not isinstance(user, User):
            raise ValueError("Provide valid `user`.")
        if getattr(user, "is_anonymous", False):
            raise PermissionError("Anonymous user not allowed.")
        if barcode is None:
            raise ValueError("Provide `barcode`.")

        # Support both dict (from DynamoDB) and Django model objects
        if isinstance(barcode, dict):
            barcode_uuid = barcode.get("barcode_uuid")
            barcode_value = barcode.get("barcode")
        else:
            barcode_uuid = str(barcode.barcode_uuid) if hasattr(barcode, "barcode_uuid") else None
            barcode_value = barcode.barcode if hasattr(barcode, "barcode") else None

        when = time_created.isoformat() if time_created else None

        item = TransactionRepository.create(
            user_id=user.id,
            barcode_uuid=barcode_uuid,
            barcode_value=barcode_value,
            time_created=when,
        )
        return item

    @staticmethod
    def bulk_ingest(
        rows: Iterable[Dict[str, Any]],
        *,
        batch_size: int = 25,
        default_time: Optional[datetime] = None,
    ) -> Sequence[CreatedTransaction]:
        """
        Bulk create Transactions from iterable of dict rows.

        Each row may contain:
          - 'user' (User instance) [required]
          - 'barcode' (dict or Barcode instance) [required]
          - 'time_created' (datetime) [optional]
        """
        items = []
        now = (default_time or timezone.now()).isoformat()

        for i, r in enumerate(rows):
            user = r.get("user")
            if not isinstance(user, User):
                raise ValueError(f"Row {i}: `user` must be a User instance.")
            if getattr(user, "is_anonymous", False):
                raise PermissionError(f"Row {i}: anonymous user not allowed.")

            barcode = r.get("barcode")
            if barcode is None:
                raise ValueError(f"Row {i}: provide `barcode`.")

            if isinstance(barcode, dict):
                barcode_uuid = barcode.get("barcode_uuid")
                barcode_value = barcode.get("barcode")
            else:
                barcode_uuid = str(barcode.barcode_uuid) if hasattr(barcode, "barcode_uuid") else None
                barcode_value = barcode.barcode if hasattr(barcode, "barcode") else None

            when = r.get("time_created")
            when_str = when.isoformat() if when else now

            items.append({
                "user_id": user.id,
                "barcode_uuid": barcode_uuid,
                "barcode_value": barcode_value,
                "time_created": when_str,
            })

        created = TransactionRepository.bulk_create(items)

        return [
            CreatedTransaction(
                txn_id=obj["sk"],
                user_id=int(obj["user_id"]),
                barcode_uuid=obj.get("barcode_uuid"),
                time_created=obj["time_created"],
            )
            for obj in created
        ]
