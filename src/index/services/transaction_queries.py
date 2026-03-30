from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence, Tuple, Dict, Any

from django.contrib.auth.models import User
from django.db.models import Count, QuerySet
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from index.models import Transaction, Barcode


class TransactionQueryMixin:
    """Read/query operations for Transaction service."""

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
            qs.values("barcode_used_id").annotate(c=Count("id")).order_by("-c")[:limit]
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

        # Optionally exclude rows whose FK points to a deleted/missing Barcode
        # (unlikely with SET_NULL)
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
