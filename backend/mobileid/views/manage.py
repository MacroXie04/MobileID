from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from mobileid.forms.ManageForm import UserBarcodeSettingsForm, BarcodeCreateForm
from mobileid.models import UserBarcodeSettings, Barcode


@login_required(login_url='login/')
def barcode_dashboard(request):
    """
    One URL → three functions:
      • edit UserBarcodeSettings
      • add a new Barcode
      • delete an existing Dynamic / Others Barcode
    """
    user = request.user
    settings_obj, _ = UserBarcodeSettings.objects.get_or_create(user=user)

    # ────────────────────────── instantiate forms ──────────────────────────
    settings_form = UserBarcodeSettingsForm(
        request.POST or None,
        instance=settings_obj,
        request=request,
        prefix="settings",
    )
    add_form = BarcodeCreateForm(request.POST or None, user=user, prefix="add")

    # ───────────────────────────── handle POST ─────────────────────────────
    if request.method == "POST":
        # 1) update settings
        if "settings-submit" in request.POST and settings_form.is_valid():
            settings_form.save()
            messages.success(request, "Barcode settings updated.")
            return redirect("mobileid:web_barcode_dashboard")

        # 2) add barcode
        if "add-submit" in request.POST and add_form.is_valid():
            add_form.save()
            messages.success(request, "New barcode added.")
            return redirect("mobileid:web_barcode_dashboard")

        # 3) delete barcode
        if "delete-submit" in request.POST:
            pk = request.POST.get("delete-barcode-pk")
            barcode = get_object_or_404(
                Barcode,
                pk=pk,
                user=user,
                barcode_type__in=["DynamicBarcode", "Others"],
            )
            barcode.delete()
            messages.success(request, "Barcode deleted.")
            return redirect("mobileid:web_barcode_dashboard")

    # ───────────────────────────── context data ────────────────────────────
    barcodes = (
        Barcode.objects
        .filter(user=user, barcode_type__in=["DynamicBarcode", "Others"])
        .order_by("-time_created")
    )

    return render(
        request,
        "../../authn/templates/manage/barcode_dashboard.html",
        {
            "settings_form": settings_form,
            "add_form": add_form,
            "barcodes": barcodes,
        },
    )
