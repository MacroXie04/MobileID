import random
from datetime import datetime, timedelta

import pytz
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import (
    render,
    redirect,
)

from barcode.settings import SELENIUM_ENABLED
from mobileid.forms.BarcodeForm import BarcodeForm
from mobileid.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
)
from mobileid.project_code.barcode import (
    uc_merced_mobile_id,
    auto_send_code,
)

from django.views.decorators.http import require_POST


@login_required(login_url="/login")
@transaction.atomic
def create_barcode(request):
    form = BarcodeForm(request.POST or None)
    # current user barcodes for delete section
    user_barcodes = Barcode.objects.filter(user=request.user).order_by('id')

    if request.method == "POST" and form.is_valid():
        src_type = form.cleaned_data["source_type"]
        input_val = form.cleaned_data["input_value"]

        if src_type == "barcode":
            response = _create_from_barcode(request.user, input_val, form)
        elif src_type == "session":
            response = _create_from_session(request.user, input_val, form)
        else:
            form.add_error("source_type", "Invalid source type.")
            response = None

        if response:
            return response

    return render(
        request,
        "index/manage_barcode.html",
        {"form": form, "user_barcodes": user_barcodes},
    )


@require_POST
@login_required(login_url="/login")
@transaction.atomic
def delete_barcode(request, pk):
    try:
        barcode_obj = Barcode.objects.select_for_update().get(pk=pk, user=request.user)
    except Barcode.DoesNotExist:
        return redirect("mobileid:manage_barcode")

    # detach barcode from settings if attached
    UserBarcodeSettings.objects.filter(user=request.user, barcode=barcode_obj).update(barcode=None)
    # optional: clean up usage tracker
    BarcodeUsage.objects.filter(barcode=barcode_obj).delete()
    barcode_obj.delete()
    return redirect("mobileid:manage_barcode")


def _link_to_user(barcode_obj: Barcode, user) -> None:
    """Attach barcode to UserBarcodeSettings in ONE query."""
    UserBarcodeSettings.objects.update_or_create(
        user=user,
        defaults={"barcode": barcode_obj},
    )


def _create_usage_if_new(barcode_obj: Barcode, is_new: bool) -> None:
    """Insert usage tracker only when barcode is newly created."""
    if is_new:
        BarcodeUsage.objects.create(barcode=barcode_obj)


# ----- source_type == "barcode" ---------------------------------------

def _create_from_barcode(user, code: str, form):
    if not code.isdigit():
        form.add_error("input_value", "Digits only.")
        return None
    else:
        if Barcode.objects.filter(barcode=code[-14:], user=user).exists():
            form.add_error("input_value", "Barcode already exists.")
            return None

    if len(code) == 16:
        # single insert query
        barcode_obj = Barcode.objects.create(
            user=user,
            barcode_type="Static",
            barcode=code,
            linked_id="",
        )
    elif len(code) == 28:
        # single insert query
        barcode_obj = Barcode.objects.create(
            user=user,
            barcode_type="Dynamic",
            barcode=code[-14:],
            linked_id="",
        )
    else:
        # single insert query
        barcode_obj = Barcode.objects.create(
            user=user,
            barcode_type="Others",
            barcode=code,
            linked_id="",
        )

    _create_usage_if_new(barcode_obj, True)
    _link_to_user(barcode_obj, user)
    return redirect("mobileid:manage_barcode")


# ----- source_type == "session" ---------------------------------------

def _create_from_session(user, session: str, form):
    if not SELENIUM_ENABLED:
        form.add_error("source_type", "Selenium is disabled.")
        return None
    if not session:
        form.add_error("input_value", "Session missing or invalid.")
        return None

    result = uc_merced_mobile_id(session)
    code = result.get("barcode")
    if not code:
        form.add_error("input_value", "Failed to retrieve barcode.")
        return None

    # try to fetch existing barcode; lock row if present
    try:
        barcode_obj, created = Barcode.objects.select_for_update().get_or_create(
            barcode=code,
            defaults={
                "user": user,
                "barcode_type": "Dynamic",
                "session": session,
                "linked_id": "",
            },
        )
    except IntegrityError:
        # rare race condition fallback
        barcode_obj = Barcode.objects.select_for_update().get(barcode=code)
        created = False

    if not created:
        # only one UPDATE query
        barcode_obj.user = user
        barcode_obj.barcode_type = "Dynamic"
        barcode_obj.session = session
        barcode_obj.save(update_fields=["user", "barcode_type", "session"])

    _create_usage_if_new(barcode_obj, created)
    _link_to_user(barcode_obj, user)
    return redirect("index")


# --------------------------------------------------------------------------- #
# Constants and helpers
# --------------------------------------------------------------------------- #
PACIFIC_TZ        = pytz.timezone("America/Los_Angeles")
CACHE_PREFIX      = "barcode_api"
POOL_TTL          = 5          # seconds: cache of barcode-linked_id pool
FLUSH_THRESHOLD   = 10         # flush counter to DB every N hits


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
# Main view
# --------------------------------------------------------------------------- #
@login_required
@transaction.atomic
def generate_barcode(request):

    # 1) Always fetch fresh user settings (no cache to reflect immediate changes)
    try:
        user_settings = (
            UserBarcodeSettings.objects
            .select_related("barcode")
            .only(
                "barcode_pull", "timestamp_verification", "server_verification",
                "barcode_id",
                "barcode__barcode", "barcode__barcode_type", "barcode__session",
            )
            .get(user_id=request.user.id)
        )
    except UserBarcodeSettings.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "User settings not found."}, status=400
        )

    # 2) Pick a barcode
    if user_settings.barcode_pull:
        # 2-a) Pull mode — get pool of candidate IDs from cache
        pool_key = f"{CACHE_PREFIX}:pool"
        pool_ids = cache.get(pool_key)

        if pool_ids is None:
            # Build pool from BarcodeUsage only (cheap)
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
                    .values_list("linked_id", flat=True)[:50 - len(pool_ids)]
                )
                pool_ids.extend(pad_ids)

            cache.set(pool_key, pool_ids, POOL_TTL)

        if not pool_ids:
            return JsonResponse(
                {"status": "error", "message": "No barcodes available."}, status=400
            )

        barcode_id = pool_ids[0]
        user_barcode = (
            Barcode.objects
            .only("barcode", "barcode_type", "session")
            .get(id=barcode_id)
        )

    else:
        # Non-pull mode — use the barcode bound to the user
        user_barcode = user_settings.barcode
        if not user_barcode:
            return JsonResponse(
                {"status": "error", "message": "No barcode assigned to user."},
                status=400,
            )

    # 3) Register usage with cached counter
    def register_usage(barcode_obj):
        # Skip if linked_id is empty, None, or not a valid integer
        if not barcode_obj.linked_id or barcode_obj.linked_id == '':
            return

        counter_key = f"{CACHE_PREFIX}:usage:{barcode_obj.linked_id}"
        count = incr_counter(counter_key)

        if count == 1 or count >= FLUSH_THRESHOLD:
            # Flush aggregate to BarcodeUsage
            try:
                updated = (
                    BarcodeUsage.objects
                    .filter(barcode_id=barcode_obj.linked_id)
                    .update(total_usage=F("total_usage") + count)
                )
                if not updated:
                    BarcodeUsage.objects.create(
                        barcode_id=barcode_obj.linked_id,
                        total_usage=count,
                    )
                cache.set(counter_key, 0, None)  # reset
            except ValueError:
                # Skip if linked_id cannot be converted to an integer
                pass


    # 4) Generate response
    if user_barcode.barcode_type.lower() == "static":
        register_usage(user_barcode)
        return JsonResponse({
            "status": "success",
            "barcode_type": "static",
            "content": f"Static: {user_barcode.barcode[-4:]}",
            "barcode": user_barcode.barcode,
        })

    if user_barcode.barcode_type.lower() == "dynamic":
        # Timestamp
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
                        pass
                    except Exception:
                        content_msg = "Server Verify Error "
            else:
                content_msg = "Server verification disabled in settings "

        elif user_settings.server_verification and user_settings.barcode_pull:
            content_msg = "Server verification skipped in pull mode "

        register_usage(user_barcode)
        return JsonResponse({
            "status": "success",
            "barcode_type": "dynamic",
            "content": f"Dynamic: {user_barcode.barcode[-4:]}",
            "barcode": f"{ts}{user_barcode.barcode}",
        })

    # Fallback
    return JsonResponse(
        {"status": "error", "message": "Invalid barcode type."}, status=400
    )
