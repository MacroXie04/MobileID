from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Sequence, Tuple, Dict, Any

from django.db import transaction as db_transaction
from django.db.models import Count, Q, QuerySet
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
    used_barcode: Optional[str]
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
    @db_transaction.atomic
    def create_transaction(
        *,
        user: User,
        barcode: Optional[Barcode] = None,
        used_barcode: Optional[str] = None,
        time_created: Optional[datetime] = None,
        save: bool = True,
    ) -> Transaction:
        """
        Create and (optionally) persist a Transaction.

        Rules:
        - At least one of (barcode, used_barcode) must be provided.
        - time_created defaults to now() if omitted.
        """
        if barcode is None and not used_barcode:
            raise ValueError("Provide at least one of `barcode` or `used_barcode`.")

        instance = Transaction(
            user=user,
            barcode_used=barcode,
            used_barcode=(used_barcode or None),
        )
        # Let auto_now_add handle normal case; allow override for backfills.
        if time_created is not None:
            # Assigning to the field directly so we can override auto_now_add.
            instance.time_created = time_created  # type: ignore[attr-defined]

        if save:
            instance.save()

        return instance

    @staticmethod
    @db_transaction.atomic
    def bulk_ingest(
        rows: Iterable[Dict[str, Any]],
        *,
        batch_size: int = 500,
        allow_missing_used_barcode: bool = False,
        default_time: Optional[datetime] = None,
    ) -> Sequence[CreatedTransaction]:
        """
        Bulk create Transactions from iterable of dict rows.

        Each row may contain:
          - 'user' (User instance)  [required]
          - 'barcode' (Barcode instance) [optional]
          - 'used_barcode' (str) [optional]
          - 'time_created' (datetime) [optional]

        Validation:
          - By default, requires (barcode or used_barcode). Override with allow_missing_used_barcode=True.
        """
        to_create: list[Transaction] = []
        now = default_time or timezone.now()

        for i, r in enumerate(rows):
            user = r.get("user")
            if not isinstance(user, User):
                raise ValueError(f"Row {i}: `user` must be a User instance.")

            barcode = r.get("barcode")
            if barcode is not None and not isinstance(barcode, Barcode):
                raise ValueError(f"Row {i}: `barcode` must be a Barcode instance or None.")

            used_barcode = r.get("used_barcode")
            if not allow_missing_used_barcode and barcode is None and not used_barcode:
                raise ValueError(f"Row {i}: provide at least one of `barcode` or `used_barcode`.")

            when = r.get("time_created") or now

            t = Transaction(
                user=user,
                barcode_used=barcode,
                used_barcode=(used_barcode or None),
            )
            # allow overriding auto_now_add
            t.time_created = when  # type: ignore[attr-defined]
            to_create.append(t)

        created = Transaction.objects.bulk_create(to_create, batch_size=batch_size)

        return [
            CreatedTransaction(
                id=obj.id,
                user_id=obj.user_id,
                barcode_id=obj.barcode_used_id,
                used_barcode=obj.used_barcode,
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
        barcode_id may be None when only used_barcode text was stored.
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
        include_text_only: bool = True,
        only_valid_barcodes: bool = False,
    ) -> Dict[str, Any]:
        """
        Static-style summary of barcode usage across the dataset.

        Returns a dict with:
          - total: total transactions in window
          - with_fk: count with a Barcode FK
          - text_only: count with used_barcode text but no FK (optional)
          - per_barcode: {<barcode_id>: count}
        """
        qs = Transaction.objects.all()
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)

        total = qs.count()
        with_fk = qs.filter(barcode_used__isnull=False).count()
        text_only_q = qs.filter(barcode_used__isnull=True, used_barcode__isnull=False)
        text_only = text_only_q.count() if include_text_only else 0

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
            "text_only": text_only,
            "per_barcode": per_barcode,
        }

    # -----------------------------
    # Convenience filters
    # -----------------------------
    @staticmethod
    def search_used_barcode_text(
        query: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
    ) -> QuerySet[Transaction]:
        """
        Case-insensitive substring match over `used_barcode` text field.
        """
        qs = Transaction.objects.filter(used_barcode__icontains=query)
        if since:
            qs = qs.filter(time_created__gte=since)
        if until:
            qs = qs.filter(time_created__lt=until)
        return qs.select_related("user", "barcode_used").order_by("-time_created")[:limit]

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
