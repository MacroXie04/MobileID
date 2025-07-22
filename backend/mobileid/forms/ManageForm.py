from django import forms
from django.contrib.auth.models import Group
from mobileid.models import UserBarcodeSettings, Barcode

YES_NO = [(True, "Yes"), (False, "No")]

def _in_group(user, group_name: str) -> bool:
    """Return True if user is in the given group."""
    return user and user.groups.filter(name=group_name).exists()


# --------------------------------------------------------------------------- #
# 1 ▸ UserBarcodeSettingsForm
# --------------------------------------------------------------------------- #
class UserBarcodeSettingsForm(forms.ModelForm):
    """
    Business rules (group‐based)
    ----------------------------
    1.  If the current user is in "User" group:
          • barcode_pull is permanently False and the widget is disabled.
    2.  When barcode_pull == True the <select> for 'barcode' must be disabled
        and any posted value rejected.
    """

    class Meta:
        model = UserBarcodeSettings
        fields = ["barcode_pull", "barcode", "server_verification"]
        widgets = {
            "barcode_pull": forms.Select(choices=YES_NO),
            "server_verification": forms.Select(choices=YES_NO),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        user = getattr(self.request, "user", None)

        # rule 1 – "User" group cannot enable pull
        if _in_group(user, "User"):
            self.fields["barcode_pull"].disabled = True
            self.initial["barcode_pull"] = False

        # rule 2 – if pull already on, lock barcode field
        if self.instance and self.instance.barcode_pull:
            self.fields["barcode"].disabled = True

        # barcode choices: all of the user’s barcodes
        if user:
            self.fields["barcode"].queryset = Barcode.objects.filter(user=user)

    def clean(self):
        cleaned = super().clean()
        user = getattr(self.request, "user", None)
        pull = cleaned.get("barcode_pull")
        bc = cleaned.get("barcode")

        # rule 1 – block "User" group from enabling pull
        if _in_group(user, "User") and pull:
            self.add_error(
                "barcode_pull",
                "Standard users cannot enable automatic barcode pull."
            )

        # rule 2 – pull ON → barcode must be empty
        if pull and bc:
            self.add_error(
                "barcode",
                "When barcode pull is ON, a specific barcode cannot be selected."
            )
            cleaned["barcode"] = None

        return cleaned


# --------------------------------------------------------------------------- #
# 2 ▸ BarcodeCreateForm
# --------------------------------------------------------------------------- #
class BarcodeCreateForm(forms.ModelForm):
    """
    • 28-digit numeric + School group → DynamicBarcode (save last 14 digits)
    • otherwise                      → Others
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
        is_school = _in_group(self.user, "School")

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
    Only allows DynamicBarcode & Others types.
    """
    barcode = forms.ModelChoiceField(queryset=Barcode.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["barcode"].queryset = Barcode.objects.filter(
            user=user,
            barcode_type__in=["DynamicBarcode", "Others"]
        )
