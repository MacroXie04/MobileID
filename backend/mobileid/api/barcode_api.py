# views.py
from datetime import datetime, timedelta
import random

from django.db import transaction
from django.db.models import F
from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import (
    status,
    serializers,
    generics,
)


from mobileid.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
)
from mobileid.project_code.barcode import (
    uc_merced_mobile_id,
    auto_send_code,
)

from mobileid.serializers.barcode import (
    BarcodeListSerializer,
    BarcodeCreateSerializer,
)

from barcode.settings import SELENIUM_ENABLED

# --------------------------------------------------------------------------- #
# Constants and helpers (reuse the originals)
# --------------------------------------------------------------------------- #
PACIFIC_TZ      = timezone.get_fixed_timezone(-480)  # America/Los_Angeles (UTC-8)
CACHE_PREFIX    = "barcode_api"
POOL_TTL        = 5
FLUSH_THRESHOLD = 10


def incr_counter(key: str) -> int:
    """
    Atomically increment a cache counter and return the new value (>= 1).
    Works across all Django cache back-ends.  If key does not exist, it is
    created with value 1.
    """
    try:
        return cache.incr(key)
    except ValueError:
        cache.add(key, 1, None)
        return 1


# --------------------------------------------------------------------------- #
# DRF view
# --------------------------------------------------------------------------- #
class GenerateBarcodeView(APIView):
    """
    Generate a static or dynamic barcode for the authenticated user.
    Pull-mode selection, timestamp / server verification, and usage
    aggregation logic are preserved from the original function-based view.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # 1) Fetch user settings (no cache)
        try:
            user_settings = (
                UserBarcodeSettings.objects
                .select_related("barcode")
                .only(
                    "barcode_pull", "timestamp_verification", "server_verification",
                    "barcode_id",
                    "barcode__barcode", "barcode__barcode_type", "barcode__session",
                )
                .get(user_id=request.user.information_id)
            )
        except UserBarcodeSettings.DoesNotExist:
            return Response(
                {"status": "error", "message": "User settings not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2) Choose a barcode
        if user_settings.barcode_pull:
            pool_key = f"{CACHE_PREFIX}:pool"
            pool_ids = cache.get(pool_key)

            if pool_ids is None:
                # Build pool from BarcodeUsage
                pool_ids = list(
                    BarcodeUsage.objects
                    .order_by("last_used", "total_usage")
                    .values_list("barcode_id", flat=True)[:50]
                )

                # Pad with unused barcodes if pool too small
                if len(pool_ids) < 50:
                    pad_ids = (
                        Barcode.objects
                        .exclude(id__in=pool_ids)
                        .values_list("information_id", flat=True)[:50 - len(pool_ids)]
                    )
                    pool_ids.extend(pad_ids)

                cache.set(pool_key, pool_ids, POOL_TTL)

            if not pool_ids:
                return Response(
                    {"status": "error", "message": "No barcodes available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            barcode_id = pool_ids[0]
            user_barcode = (
                Barcode.objects
                .only("barcode", "barcode_type", "session")
                .get(id=barcode_id)
            )
        else:
            # Non-pull mode
            user_barcode = user_settings.barcode
            if not user_barcode:
                return Response(
                    {"status": "error", "message": "No barcode assigned to user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 3) Helper to register usage counts
        def register_usage(barcode_obj):
            # Skip if information_id is empty, None, or not a valid integer
            if not barcode_obj.information_id or barcode_obj.information_id == '':
                return

            counter_key = f"{CACHE_PREFIX}:usage:{barcode_obj.information_id}"
            count = incr_counter(counter_key)

            if count == 1 or count >= FLUSH_THRESHOLD:
                try:
                    updated = (
                        BarcodeUsage.objects
                        .filter(barcode_id=barcode_obj.information_id)
                        .update(total_usage=F("total_usage") + count)
                    )
                    if not updated:
                        BarcodeUsage.objects.create(
                            barcode_id=barcode_obj.information_id,
                            total_usage=count,
                        )
                    cache.set(counter_key, 0, None)  # reset counter
                except ValueError:
                    # Skip if information_id cannot be converted to an integer
                    pass

        # 4) Build response for static barcodes
        if user_barcode.barcode_type.lower() == "static":
            register_usage(user_barcode)
            return Response({
                "status": "success",
                "barcode_type": "static",
                "content": f"Static: {user_barcode.barcode[-4:]}",
                "barcode": user_barcode.barcode,
            })

        # 5) Build response for dynamic barcodes
        if user_barcode.barcode_type.lower() == "dynamic":
            # Timestamp handling
            if user_settings.timestamp_verification:
                ts = datetime.now(PACIFIC_TZ).strftime("%Y%m%d%H%M%S")
            else:
                start = datetime.now() - timedelta(days=365)
                ts_rand = random.randint(0, int((datetime.now() - start).total_seconds()))
                ts = (start + timedelta(seconds=ts_rand)).strftime("%Y%m%d%H%M%S")

            # Optional server verification
            content_msg = ""
            if user_settings.server_verification and not user_settings.barcode_pull:
                if SELENIUM_ENABLED:
                    session = user_barcode.session
                    if not session:
                        content_msg = "field to verify server "
                    else:
                        try:
                            server_res = auto_send_code(session)
                            if server_res.get("status") == "success":
                                content_msg = f"Server Verify OK: {server_res['code']} "
                            else:
                                content_msg = "Server Verify Failed "
                                user_barcode.session = None
                                user_barcode.save(update_fields=["session"])
                        except Exception:
                            content_msg = "Server Verify Error "
                else:
                    content_msg = "Server verification disabled in settings "

            elif user_settings.server_verification and user_settings.barcode_pull:
                content_msg = "Server verification skipped in pull mode "

            register_usage(user_barcode)
            return Response({
                "status": "success",
                "barcode_type": "dynamic",
                "content": f"Dynamic: {user_barcode.barcode[-4:]} {content_msg}".strip(),
                "barcode": f"{ts}{user_barcode.barcode}",
            })

        # 6) Fallback
        return Response(
            {"status": "error", "message": "Invalid barcode type."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BarcodeListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BarcodeCreateSerializer
        return BarcodeListSerializer

    def get_queryset(self):
        return Barcode.objects.filter(user=self.request.user).order_by('-information_id')

    def perform_create(self, serializer):
        serializer.save()


class BarcodeDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Barcode.objects.all()

    def get_queryset(self):
        # user can only delete their own barcodes
        return super().get_queryset().filter(user=self.request.user)

    def perform_destroy(self, instance):
        # remove barcode from user settings and delete usage records
        UserBarcodeSettings.objects.filter(user=self.request.user, barcode=instance).update(barcode=None)
        BarcodeUsage.objects.filter(barcode=instance).delete()
        instance.delete()
