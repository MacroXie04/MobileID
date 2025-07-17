"""
forms.py
~~~~~~~~
Forms for the barcode dashboard.

* UserBarcodeSettingsForm – edit pull / verification flags & choose default barcode
* BarcodeCreateForm       – add a new barcode (type auto-assigned)
* BarcodeDeleteForm       – confirm deletion of one existing barcode
"""

from django import forms

from mobileid.models import UserBarcodeSettings, Barcode

YES_NO = [(True, "Yes"), (False, "No")]  # shared dropdown values


# --------------------------------------------------------------------------- #
# 1 ▸ UserBarcodeSettingsForm
# --------------------------------------------------------------------------- #
class UserBarcodeSettingsForm(forms.ModelForm):
    """
    Business rules
    --------------
    1.  If the current user’s UserAccount.account_type == "User":
          • barcode_pull is permanently False and the widget is disabled.
    2.  When barcode_pull == True the <select> for 'barcode' must be disabled
        and a POST that tries to send a value is rejected.
    """

    class Meta:
        model = UserBarcodeSettings
        fields = ["barcode_pull", "barcode", "server_verification"]
        widgets = {
            "barcode_pull": forms.Select(choices=YES_NO),
            "server_verification": forms.Select(choices=YES_NO),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)  # injected by the view
        super().__init__(*args, **kwargs)

        user = getattr(self.request, "user", None)

        # rule 1 – standard “User” accounts cannot enable pull
        if user and hasattr(user, "useraccount"):
            if user.useraccount.account_type == "User":
                self.fields["barcode_pull"].disabled = True
                self.initial["barcode_pull"] = False

        # rule 2 – if pull already on, lock barcode field in UI
        if self.instance and self.instance.barcode_pull:
            self.fields["barcode"].disabled = True

        # barcode choices: **all** of the user’s barcodes (no type filter)
        if user:
            self.fields["barcode"].queryset = Barcode.objects.filter(user=user)

    def clean(self):
        cleaned = super().clean()
        barcode_pull = cleaned.get("barcode_pull")
        barcode_obj = cleaned.get("barcode")
        user = getattr(self.request, "user", None)

        # rule 1 – block “User” accounts changing pull
        if user and hasattr(user, "useraccount"):
            if user.useraccount.account_type == "User" and barcode_pull:
                self.add_error(
                    "barcode_pull", "Standard users cannot enable automatic barcode pull."
                )

        # rule 2 – pull ON → barcode must be empty
        if barcode_pull and barcode_obj:
            self.add_error(
                "barcode",
                "When barcode pull is ON, a specific barcode cannot be selected.",
            )
            cleaned["barcode"] = None

        return cleaned


# --------------------------------------------------------------------------- #
# 2 ▸ BarcodeCreateForm
# --------------------------------------------------------------------------- #
class BarcodeCreateForm(forms.ModelForm):
    """
    • 28-digit numeric  + School account  → DynamicBarcode (save last 14 digits)
    • otherwise                           → Others
    """

    class Meta:
        model = Barcode
        fields = ["barcode"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_barcode(self):
        return self.cleaned_data["barcode"].strip()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.user = self.user

        code = obj.barcode
        is_28 = len(code) == 28 and code.isdigit()
        is_school = (
                hasattr(self.user, "useraccount")
                and self.user.useraccount.account_type == "School"
        )

        if is_28 and is_school:
            obj.barcode_type = "DynamicBarcode"
            obj.barcode = code[-14:]
        else:
            obj.barcode_type = "Others"

        if commit:
            obj.save()
        return obj


# --------------------------------------------------------------------------- #
# 3 ▸ BarcodeDeleteForm
# --------------------------------------------------------------------------- #
class BarcodeDeleteForm(forms.Form):
    """
    Confirmation form for deleting a barcode.
    Only allows DynamicBarcode & Other types (Identification never deletable here).
    """

    barcode = forms.ModelChoiceField(queryset=Barcode.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")  # required
        super().__init__(*args, **kwargs)
        self.fields["barcode"].queryset = Barcode.objects.filter(
            user=user, barcode_type__in=["DynamicBarcode", "Other"]
        )
