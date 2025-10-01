from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Sequence, Tuple, Dict, Any

from django.db import transaction as db_transaction
from django.db.models import Count, QuerySet
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.utils import timezone

from index.models import (
    Transaction,
    User,
    Barcode,
)


@dataclass(frozen=True)
class CreatedTransaction:
    """Lightweight return type for bulk_create summaries."""
    id: int
    user_id: int
    barcode_id: Optional[int]
    time_created: datetime


class TransactionService:
    """
    Service layer for Transaction-related reads/writes.
    Keeps your views thin and reusable for Celery tasks, management commands, etc.
    """

    # -----------------------------
    # Writes
    # -----------------------------
    @staticmethod
    # database transaction decorator (disable for development)
    # @db_transaction.atomic
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
        - `user` must be a valid, active User.
        - `barcode` must be provided.
        - time_created defaults to now() if omitted.
        """
        # Validate user instance
        if not isinstance(user, User):
            raise ValueError("Provide valid `user`.")

        # Disallow anonymous/inactive users
        if getattr(user, "is_anonymous", False):
            raise PermissionError("Anonymous user not allowed.")
        if hasattr(user, "is_active") and not user.is_active:
            raise PermissionError("Inactive user not allowed.")

        # Validate barcode instance
        if barcode is None:
            raise ValueError("Provide `barcode`.")
        if not isinstance(barcode, Barcode):
            raise ValueError("`barcode` must be a Barcode instance.")

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
    # database transaction decorator (disable for development)
    # @db_transaction.atomic
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
          - 'user' must be active.
        """
        to_create: list[Transaction] = []
        now = default_time or timezone.now()

        for i, r in enumerate(rows):
            user = r.get("user")
            if not isinstance(user, User):
                raise ValueError(f"Row {i}: `user` must be a User instance.")
            if getattr(user, "is_anonymous", False):
                raise PermissionError(f"Row {i}: anonymous user not allowed.")
            if hasattr(user, "is_active") and not user.is_active:
                raise PermissionError(f"Row {i}: inactive user not allowed.")

            barcode = r.get("barcode")
            if barcode is not None and not isinstance(barcode, Barcode):
                raise ValueError(f"Row {i}: `barcode` must be a Barcode instance or None.")
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

    # -----------------------------
    # Reads / Query helpers
    # -----------------------------
    @staticmethod
    def for_user(
        user: User,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        select_related: bool = True,
    ) -> QuerySet[Transaction]:
        qs = Transaction.objects.filter(user=user)
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)
        if select_related:
            qs = qs.select_related("user", "barcode_used")
        return qs.order_by("-time_created")

    @staticmethod
    def top_barcodes(
        *,
        limit: int = 10,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Sequence[Tuple[Optional[int], int]]:
        """
        Return [(barcode_id, count), ...] ordered by count desc.
        """
        qs = Transaction.objects.all()
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)

        agg = (
            qs.values("barcode_used_id")
            .annotate(c=Count("id"))
            .order_by("-c")[:limit]
        )
        return [(row["barcode_used_id"], row["c"]) for row in agg]

    @staticmethod
    def usage_over_time(
        *,
        granularity: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Sequence[Tuple[datetime, int]]:
        """
        Group usage counts by time bucket.
        granularity: 'day' | 'week' | 'month'
        """
        trunc_map = {
            "day": TruncDay,
            "week": TruncWeek,
            "month": TruncMonth,
        }
        if granularity not in trunc_map:
            raise ValueError("granularity must be 'day', 'week', or 'month'.")

        qs = Transaction.objects.all()
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)

        TruncFn = trunc_map[granularity]
        agg = (
            qs.annotate(bucket=TruncFn("time_created"))
            .values("bucket")
            .annotate(c=Count("id"))
            .order_by("bucket")
        )
        return [(row["bucket"], row["c"]) for row in agg]

    # -----------------------------
    # Barcode usage stats (static)
    # -----------------------------
    @staticmethod
    def barcode_usage_stats(
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        only_valid_barcodes: bool = False,
    ) -> Dict[str, Any]:
        """
        Static-style summary of barcode usage across the dataset.

        Returns a dict with:
          - total: total transactions in window
          - with_fk: count with a Barcode FK
          - per_barcode: {<barcode_id>: count}
        """
        qs = Transaction.objects.all()
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)

        total = qs.count()
        with_fk = qs.filter(barcode_used__isnull=False).count()

        # Optionally exclude rows whose FK points to a deleted/missing Barcode (unlikely with SET_NULL)
        per_barcode_qs = qs
        if only_valid_barcodes:
            per_barcode_qs = per_barcode_qs.filter(barcode_used__isnull=False)

        per_barcode_rows = (
            per_barcode_qs.values("barcode_used_id")
            .annotate(c=Count("id"))
            .order_by("-c")
        )
        per_barcode = {
            str(row["barcode_used_id"]): row["c"] for row in per_barcode_rows
        }

        return {
            "total": total,
            "with_fk": with_fk,
            "per_barcode": per_barcode,
        }

    # -----------------------------
    # Convenience filters
    # -----------------------------

    @staticmethod
    def for_barcode(
        barcode: Barcode,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> QuerySet[Transaction]:
        qs = Transaction.objects.filter(barcode_used=barcode)
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)
        return qs.select_related("user", "barcode_used").order_by("-time_created")
