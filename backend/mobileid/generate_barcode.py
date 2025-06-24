import random
from datetime import datetime, timedelta

import pytz
from django.db import transaction
from django.db.models import F, Value, IntegerField, DateTimeField
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mobileid.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeUsage,
    UserBarcodeSettings,
)
from mobileid.project_code.barcode import auto_send_code

from barcode.settings import SELENIUM_ENABLED

CALIFORNIA_TZ = pytz.timezone("America/Los_Angeles")
# default for “never-used” barcodes
EPOCH = datetime(1970, 1, 1, tzinfo=pytz.UTC)


# ----------------------------------------------------------------------
# Helper: record one barcode use (thread-safe)
# ----------------------------------------------------------------------
def update_usage(barcode: Barcode, user):
    """
    1. Insert a UserBarcodeUsage row (per-use log)
    2. Atomically increment total_usage and refresh last_used in BarcodeUsage
    """
    with transaction.atomic():
        # Per-use log
        UserBarcodeUsage.objects.create(user=user, barcode=barcode)

        # Aggregate counter (create if missing)
        usage_row, _ = BarcodeUsage.objects.get_or_create(barcode=barcode)
        BarcodeUsage.objects.filter(pk=usage_row.pk).update(
            # auto_now=True handles last_used
            total_usage=F("total_usage") + 1
        )


def generate(user):


    # ---------- Load user settings ----------
    try:
        user_settings = UserBarcodeSettings.objects.select_related("barcode").get(user=user)
    except UserBarcodeSettings.DoesNotExist:
        return Response({"status": "error", "message": "User settings not found."})

    # ---------- Pick a barcode ----------
    if user_settings.barcode_pull:  # pooled selection
        candidate = (
            Barcode.objects.annotate(
                usage_cnt=Coalesce("barcodeusage__total_usage", Value(0), output_field=IntegerField()),
                last_used=Coalesce("barcodeusage__last_used", Value(EPOCH), output_field=DateTimeField()),
            )
            .order_by("usage_cnt", "last_used")
            .first()
        )
        if not candidate:
            return Response({"status": "error", "message": "No barcodes available."})
        barcode = candidate
    else:
        barcode = user_settings.barcode
        if not barcode:
            return Response({"status": "error", "message": "No barcode assigned to user."})

    # ---------- Timestamp generation ----------
    if user_settings.timestamp_verification:
        time_stamp = timezone.now().astimezone(CALIFORNIA_TZ).strftime("%Y%m%d%H%M%S")
    else:
        start_date = timezone.now() - timedelta(days=365)
        random_seconds = random.randint(0, int((timezone.now() - start_date).total_seconds()))
        random_datetime = start_date + timedelta(seconds=random_seconds)
        time_stamp = random_datetime.strftime("%Y%m%d%H%M%S")

    # ---------- Handle barcode types ----------
    barcode_type = barcode.barcode_type.lower()

    if barcode_type == "static":
        update_usage(barcode, user)
        return Response(
            {
                "status": "success",
                "barcode_type": "static",
                "content": f"Static: Ending with {barcode.barcode[-4:]}",
                "barcode": barcode.barcode,
            }
        )

    if barcode_type == "dynamic":
        # Optional server verification
        content_msg = ""
        if user_settings.server_verification and not user_settings.barcode_pull:
            if not barcode.session:
                content_msg = "Session is missing "
            else:
                try:
                    server_result = auto_send_code(barcode.session)
                    if server_result["status"] == "success":
                        content_msg = f"Server Verification Success: {server_result['code']} "
                    else:
                        content_msg = "Server Verification Failed "
                        barcode.session = None
                        barcode.save(update_fields=["session"])
                except Exception:
                    content_msg = "Server Verification Error "

        # Record usage
        update_usage(barcode, user)

        return Response(
            {
                "status": "success",
                "barcode_type": "dynamic",
                "content": f"{content_msg}Dynamic: Ending with {barcode.barcode[-4:]}",
                "barcode": f"{time_stamp}{barcode.barcode}",
            }
        )

    # ---------- Unsupported type ----------
    return Response({"status": "error", "message": "Invalid barcode type."})
