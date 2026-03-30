from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Sequence, Dict, Any

from django.contrib.auth.models import User
from django.utils import timezone
from index.models import Transaction, Barcode


@dataclass(frozen=True)
class CreatedTransaction:
    """Lightweight return type for bulk_create summaries."""

    id: int
    user_id: int
    barcode_id: Optional[int]
    time_created: datetime


class TransactionWriteMixin:
    """Write operations for Transaction service."""

    @staticmethod
    def create_transaction(
        *,
        user: User,
        barcode: Optional[Barcode] = None,
        time_created: Optional[datetime] = None,
        save: bool = True,
    ) -> Transaction:
        """
        Create and (optionally) persist a Transaction.

        Rules:
        - `user` must be a valid User.
        - `barcode` must be provided.
        - time_created defaults to now() if omitted.
        """
        # Validate user instance
        if not isinstance(user, User):
            raise ValueError("Provide valid `user`.")

        # Disallow anonymous users
        if getattr(user, "is_anonymous", False):
            raise PermissionError("Anonymous user not allowed.")

        # Validate barcode instance
        if barcode is None:
            raise ValueError("Provide `barcode`.")
        if not isinstance(barcode, Barcode):
            raise ValueError("`barcode` must be a Barcode instance.")
        # Ownership is not enforced here; allow recording transactions
        # even when the acting user differs from the barcode owner.

        instance = Transaction(
            user=user,
            barcode_used=barcode,
        )
        # Let auto_now_add handle normal case; allow override for backfills.
        if time_created is not None:
            # Assigning to the field directly so we can override auto_now_add.
            instance.time_created = time_created

        if save:
            instance.save()

        return instance

    @staticmethod
    def bulk_ingest(
        rows: Iterable[Dict[str, Any]],
        *,
        batch_size: int = 500,
        default_time: Optional[datetime] = None,
    ) -> Sequence[CreatedTransaction]:
        """
        Bulk create Transactions from iterable of dict rows.

        Each row may contain:
          - 'user' (User instance)  [required]
          - 'barcode' (Barcode instance) [optional]
          - 'time_created' (datetime) [optional]

        Validation:
          - Requires 'barcode'.
          - 'user' must be a User instance.
        """
        to_create: list[Transaction] = []
        now = default_time or timezone.now()

        for i, r in enumerate(rows):
            user = r.get("user")
            if not isinstance(user, User):
                raise ValueError(f"Row {i}: `user` must be a User instance.")
            if getattr(user, "is_anonymous", False):
                raise PermissionError(f"Row {i}: anonymous user not allowed.")

            barcode = r.get("barcode")
            if barcode is not None and not isinstance(barcode, Barcode):
                raise ValueError(
                    f"Row {i}: `barcode` must be a Barcode instance or None."
                )
            if barcode is None:
                raise ValueError(f"Row {i}: provide `barcode`.")
            # Ownership is not required; allow recording transactions where the
            # acting user differs from the barcode owner.

            when = r.get("time_created") or now

            t = Transaction(
                user=user,
                barcode_used=barcode,
                time_created=when,
            )
            to_create.append(t)

        created = Transaction.objects.bulk_create(to_create, batch_size=batch_size)

        return [
            CreatedTransaction(
                id=obj.id,
                user_id=obj.user_id,
                barcode_id=obj.barcode_used_id,
                time_created=obj.time_created,
            )
            for obj in created
        ]
