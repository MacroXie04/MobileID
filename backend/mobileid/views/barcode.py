from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect

from barcode.settings import SELENIUM_ENABLED
from mobileid.forms.BarcodeForm import BarcodeForm
from mobileid.models import Barcode, BarcodeUsage, UserBarcodeSettings
from mobileid.project_code.barcode import uc_merced_mobile_id


@login_required(login_url="/login")
@transaction.atomic
def create_barcode(request):
    form = BarcodeForm(request.POST or None)

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

        if response:  # redirect already prepared
            return response  # ← one DB roundtrip ends here

    return render(request, "index/create_barcode.html", {"form": form})


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
    if len(code) not in (16, 28):
        form.add_error("input_value", "Barcode length not invalid.")
        return None
    if len(code) == 16:
        if Barcode.objects.filter(barcode=code, user=user).exists():
            form.add_error("input_value", "Barcode already exists.")
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
            student_id="",
        )
    else:
        # single insert query
        barcode_obj = Barcode.objects.create(
            user=user,
            barcode_type="Dynamic",
            barcode=code[-14:],
            student_id="",
        )

    _create_usage_if_new(barcode_obj, True)
    _link_to_user(barcode_obj, user)
    return redirect("mobileid:index")


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
                "student_id": "",
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
