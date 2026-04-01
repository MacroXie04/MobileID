from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Optional, Tuple

from django.utils import timezone

from index.repositories import BarcodeRepository, TransactionRepository


class UsageLimitService:
    """Service for checking and enforcing barcode usage limits."""

    @staticmethod
    def _today_window() -> tuple[str, str]:
        """
        Return the start and end ISO timestamps for "today" in the current timezone.
        """
        local_tz = timezone.get_current_timezone()
        today_date = timezone.localdate()

        start_local = datetime.combine(today_date, time.min, tzinfo=local_tz)
        end_local = start_local + timedelta(days=1)

        return start_local.isoformat(), end_local.isoformat()

    @staticmethod
    def check_daily_limit(barcode: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if barcode has exceeded its daily usage limit.

        Args:
            barcode: Dict with barcode data (from DynamoDB or repository).
        """
        daily_limit = int(barcode.get("daily_usage_limit", 0))

        if daily_limit == 0:
            return True, None

        start_of_day, end_of_day = UsageLimitService._today_window()

        today_count = TransactionRepository.count_for_barcode_since(
            barcode_uuid=barcode["barcode_uuid"],
            since=start_of_day,
        )

        if today_count >= daily_limit:
            return (
                False,
                f"Daily usage limit of {daily_limit} scans has been reached",
            )

        return True, None

    @staticmethod
    def check_total_limit(barcode: dict) -> Tuple[bool, Optional[str]]:
        """Check if barcode has exceeded its total usage limit."""
        total_limit = int(barcode.get("total_usage_limit", 0))

        if total_limit == 0:
            return True, None

        total_usage = int(barcode.get("total_usage", 0))
        if total_usage >= total_limit:
            return (
                False,
                f"Total usage limit of {total_limit} scans has been reached",
            )

        return True, None

    @staticmethod
    def check_all_limits(barcode: dict) -> Tuple[bool, Optional[str]]:
        """Check both daily and total usage limits."""
        allowed, error = UsageLimitService.check_daily_limit(barcode)
        if not allowed:
            return allowed, error
        return UsageLimitService.check_total_limit(barcode)

    @staticmethod
    def get_usage_stats(barcode: dict) -> dict:
        """Get current usage statistics for a barcode."""
        daily_limit = int(barcode.get("daily_usage_limit", 0))
        total_limit = int(barcode.get("total_usage_limit", 0))
        total_usage = int(barcode.get("total_usage", 0))

        start_of_day, _ = UsageLimitService._today_window()
        daily_used = TransactionRepository.count_for_barcode_since(
            barcode_uuid=barcode["barcode_uuid"],
            since=start_of_day,
        )

        return {
            "daily_used": daily_used,
            "daily_limit": daily_limit,
            "total_used": total_usage,
            "total_limit": total_limit,
            "daily_remaining": (
                None if daily_limit == 0 else max(0, daily_limit - daily_used)
            ),
            "total_remaining": (
                None if total_limit == 0 else max(0, total_limit - total_usage)
            ),
        }
