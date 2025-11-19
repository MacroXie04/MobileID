from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Optional, Tuple

from django.utils import timezone
from index.models import Barcode, BarcodeUsage, Transaction


class UsageLimitService:
    """Service for checking and enforcing barcode usage limits."""

    @staticmethod
    def _today_window() -> tuple[datetime, datetime]:
        """
        Return the start and end datetimes for "today" in the current timezone.

        We must compute boundaries in the active timezone (settings.TIME_ZONE)
        instead of naive UTC midnight. Otherwise, daily counts won't reset at
        local midnight and will appear to "not refresh" until UTC midnight.
        """
        # "Today" as a date in the current timezone
        local_tz = timezone.get_current_timezone()
        today_date = timezone.localdate()

        # Start of local day (aware)
        start_local = datetime.combine(today_date, time.min, tzinfo=local_tz)
        # End boundary is start of next local day (half-open interval)
        end_local = start_local + timedelta(days=1)

        return start_local, end_local

    @staticmethod
    def check_daily_limit(barcode: Barcode) -> Tuple[bool, Optional[str]]:
        """
        Check if barcode has exceeded its daily usage limit.

        Returns:
            (is_allowed, error_message)
            - is_allowed: True if usage is allowed, False if limit exceeded
            - error_message: Human-readable error message if limit exceeded
        """
        try:
            usage = BarcodeUsage.objects.get(barcode=barcode)

            # If no daily limit is set (0), allow usage
            if usage.daily_usage_limit == 0:
                return True, None

            # Count only transactions within the local-day window
            start_of_day, end_of_day = UsageLimitService._today_window()

            # Count today's transactions for this barcode
            today_count = Transaction.objects.filter(
                barcode_used=barcode,
                time_created__gte=start_of_day,
                time_created__lt=end_of_day,
            ).count()

            if today_count >= usage.daily_usage_limit:
                return (
                    False,
                    f"Daily usage limit of {usage.daily_usage_limit} scans has been reached",
                )

            return True, None

        except BarcodeUsage.DoesNotExist:
            # If no usage record exists, allow usage (will be created on first use)
            return True, None

    @staticmethod
    def check_total_limit(barcode: Barcode) -> Tuple[bool, Optional[str]]:
        """
        Check if barcode has exceeded its total usage limit.

        Returns:
            (is_allowed, error_message)
        """
        try:
            usage = BarcodeUsage.objects.get(barcode=barcode)

            # If no total limit is set (0), allow usage
            if usage.total_usage_limit == 0:
                return True, None

            if usage.total_usage >= usage.total_usage_limit:
                return (
                    False,
                    f"Total usage limit of {usage.total_usage_limit} scans has been reached",
                )

            return True, None

        except BarcodeUsage.DoesNotExist:
            # If no usage record exists, allow usage
            return True, None

    @staticmethod
    def check_all_limits(barcode: Barcode) -> Tuple[bool, Optional[str]]:
        """
        Check both daily and total usage limits.

        Returns:
            (is_allowed, error_message)
        """
        # Check daily limit first
        allowed, error = UsageLimitService.check_daily_limit(barcode)
        if not allowed:
            return allowed, error

        # Then check total limit
        return UsageLimitService.check_total_limit(barcode)

    @staticmethod
    def get_usage_stats(barcode: Barcode) -> dict:
        """
        Get current usage statistics for a barcode.

        Returns dict with:
            - daily_used: Number of uses today
            - daily_limit: Daily limit (0 means no limit)
            - total_used: Total uses all time
            - total_limit: Total limit (0 means no limit)
            - daily_remaining: Remaining uses today (None if no limit)
            - total_remaining: Remaining uses total (None if no limit)
        """
        try:
            usage = BarcodeUsage.objects.get(barcode=barcode)

            # Count today's usage in local-day window
            start_of_day, end_of_day = UsageLimitService._today_window()
            daily_used = Transaction.objects.filter(
                barcode_used=barcode,
                time_created__gte=start_of_day,
                time_created__lt=end_of_day,
            ).count()

            return {
                "daily_used": daily_used,
                "daily_limit": usage.daily_usage_limit,
                "total_used": usage.total_usage,
                "total_limit": usage.total_usage_limit,
                "daily_remaining": (
                    None
                    if usage.daily_usage_limit == 0
                    else max(0, usage.daily_usage_limit - daily_used)
                ),
                "total_remaining": (
                    None
                    if usage.total_usage_limit == 0
                    else max(0, usage.total_usage_limit - usage.total_usage)
                ),
            }
        except BarcodeUsage.DoesNotExist:
            return {
                "daily_used": 0,
                "daily_limit": 0,
                "total_used": 0,
                "total_limit": 0,
                "daily_remaining": None,
                "total_remaining": None,
            }
