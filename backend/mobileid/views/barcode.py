from datetime import datetime, timedelta

import pytz
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from mobileid.forms.BarcodeForm import BarcodeForm
from mobileid.models import Barcode, BarcodeUsage, UserBarcodeSettings

from mobileid.services.barcode import generate_barcode


@login_required(login_url="/login")
@transaction.atomic
def create_barcode(request):
    form = BarcodeForm(request.POST or None)
    # current user barcodes for delete section
    user_barcodes = Barcode.objects.filter(user=request.user).order_by("id")

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
        return redirect("mobileid:web_manage_barcode")

    # detach barcode from settings if attached
    UserBarcodeSettings.objects.filter(user=request.user, barcode=barcode_obj).update(
        barcode=None
    )
    # optional: clean up usage tracker
    BarcodeUsage.objects.filter(barcode=barcode_obj).delete()
    barcode_obj.delete()
    return redirect("mobileid:web_manage_barcode")


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
    return redirect("mobileid:web_manage_barcode")


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
    return redirect("mobileid:web_index")


# --------------------------------------------------------------------------- #
# Constants and helpers
# --------------------------------------------------------------------------- #
PACIFIC_TZ = pytz.timezone("America/Los_Angeles")
CACHE_PREFIX = "barcode_api"
POOL_TTL = 5  # seconds: cache of barcode-linked_id pool
FLUSH_THRESHOLD = 10  # flush counter to DB every N hits


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



@login_required(login_url="/login")
@transaction.atomic
def generate_barcode_view(request):
    result = generate_barcode(request.user)
    return JsonResponse(result)