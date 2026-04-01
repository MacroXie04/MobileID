from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional, Sequence, Tuple, Dict, Any

from index.repositories import TransactionRepository


class TransactionQueryMixin:
    """Read/query operations for Transaction service (DynamoDB-backed)."""

    @staticmethod
    def for_user(
        user,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[dict]:
        since_str = since.isoformat() if since else None
        until_str = until.isoformat() if until else None
        return TransactionRepository.for_user(
            user_id=user.id if hasattr(user, "id") else user,
            since=since_str,
            until=until_str,
        )

    @staticmethod
    def top_barcodes(
        *,
        limit: int = 10,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Sequence[Tuple[Optional[str], int]]:
        """
        Return [(barcode_uuid, count), ...] ordered by count desc.

        NOTE: This requires a table scan. Acceptable for admin analytics,
        not for hot-path queries.
        """
        # Scan-based aggregation — acceptable for low-frequency admin queries
        from core.dynamodb.client import get_table

        table = get_table("transactions")
        counter: Counter = Counter()

        kwargs = {}
        last_key = None
        while True:
            if last_key:
                kwargs["ExclusiveStartKey"] = last_key
            resp = table.scan(**kwargs)
            for item in resp.get("Items", []):
                tc = item.get("time_created", "")
                if since and tc < since.isoformat():
                    continue
                if until and tc >= until.isoformat():
                    continue
                bc_uuid = item.get("barcode_uuid")
                counter[bc_uuid] += 1

            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break

        return counter.most_common(limit)

    @staticmethod
    def usage_over_time(
        *,
        granularity: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Sequence[Tuple[str, int]]:
        """
        Group usage counts by time bucket.

        Returns [(bucket_key, count), ...] where bucket_key is a date string.
        NOTE: Scan-based — admin-only.
        """
        from core.dynamodb.client import get_table

        table = get_table("transactions")
        buckets: Counter = Counter()

        kwargs = {}
        last_key = None
        while True:
            if last_key:
                kwargs["ExclusiveStartKey"] = last_key
            resp = table.scan(**kwargs)
            for item in resp.get("Items", []):
                tc = item.get("time_created", "")
                if since and tc < since.isoformat():
                    continue
                if until and tc >= until.isoformat():
                    continue

                # Truncate to bucket
                if granularity == "day":
                    bucket = tc[:10]  # YYYY-MM-DD
                elif granularity == "week":
                    try:
                        dt = datetime.fromisoformat(tc)
                        # ISO week start (Monday)
                        week_start = dt - __import__("datetime").timedelta(
                            days=dt.weekday()
                        )
                        bucket = week_start.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        continue
                elif granularity == "month":
                    bucket = tc[:7]  # YYYY-MM
                else:
                    raise ValueError("granularity must be 'day', 'week', or 'month'.")

                buckets[bucket] += 1

            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break

        return sorted(buckets.items())

    @staticmethod
    def barcode_usage_stats(
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        only_valid_barcodes: bool = False,
    ) -> Dict[str, Any]:
        """Scan-based barcode usage stats — admin-only."""
        from core.dynamodb.client import get_table

        table = get_table("transactions")
        total = 0
        with_fk = 0
        per_barcode: Counter = Counter()

        kwargs = {}
        last_key = None
        while True:
            if last_key:
                kwargs["ExclusiveStartKey"] = last_key
            resp = table.scan(**kwargs)
            for item in resp.get("Items", []):
                tc = item.get("time_created", "")
                if since and tc < since.isoformat():
                    continue
                if until and tc >= until.isoformat():
                    continue

                total += 1
                bc_uuid = item.get("barcode_uuid")
                if bc_uuid:
                    with_fk += 1
                    per_barcode[bc_uuid] += 1

            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break

        return {
            "total": total,
            "with_fk": with_fk,
            "per_barcode": dict(per_barcode),
        }

    @staticmethod
    def for_barcode(
        barcode_uuid: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[dict]:
        since_str = since.isoformat() if since else None
        until_str = until.isoformat() if until else None
        return TransactionRepository.for_barcode(
            barcode_uuid=barcode_uuid,
            since=since_str,
            until=until_str,
        )
