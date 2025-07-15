from django import forms

from mobileid.models import UserProfile

from io import BytesIO
import base64
from PIL import Image
from django.core.files.uploadedfile import UploadedFile
from django import forms
from mobileid.models import UserProfile

def _pil_to_base64(pil):
    s = min(pil.size)
    x0 = (pil.width - s) // 2
    y0 = (pil.height - s) // 2
    pil = pil.crop((x0, y0, x0 + s, y0 + s)).resize((128, 128), Image.LANCZOS)
    buf = BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class InformationUpdateForm(forms.ModelForm):
    # New upload (hidden via CSS)
    user_profile_img = forms.ImageField(required=False, label="")
    # Base64 copy of current / cropped avatar
    user_profile_img_base64 = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="",
    )

    class Meta:
        model = UserProfile
        fields = ("name", "information_id", "user_profile_img", "user_profile_img_base64")

    # ---------- helpers ---------- #
    @staticmethod
    def _pil_to_base64(pil_img):
        """128 × 128 PNG → Base64 (strip header)."""
        s = min(pil_img.size)
        x0 = (pil_img.width - s) // 2
        y0 = (pil_img.height - s) // 2
        pil_img = pil_img.crop((x0, y0, x0 + s, y0 + s)).resize((128, 128), Image.LANCZOS)
        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    # ---------- main save ---------- #
    def save(self, commit=True):
        profile = super().save(commit=False)

        img_file  = self.cleaned_data.get("user_profile_img")
        base64str = self.cleaned_data.get("user_profile_img_base64")

        # --- Case 1: user picked a *new* file -------------------------
        if isinstance(img_file, UploadedFile):
            with Image.open(img_file) as im:
                profile.user_profile_img = _pil_to_base64(im)

        # --- Case 2: keep / update existing Base64 --------------------
        elif base64str:
            profile.user_profile_img = base64str

        # Case 3: neither changed → leave avatar untouched

        if commit:
            profile.save()
        return profile


import base64
from io import BytesIO

from django import forms
from PIL import Image

from mobileid.models import Barcode, UserBarcodeSettings







class UserBarcodeSettingsForm(forms.ModelForm):
    # Common boolean dropdown choices
    BOOL_CHOICES = (
        (True, "Yes"),
        (False, "No"),
    )

    # Boolean fields rendered as dropdowns
    barcode_pull = forms.TypedChoiceField(
        label="Enable Barcode Pull",
        choices=BOOL_CHOICES,
        coerce=lambda x: x in (True, "True", "true"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    server_verification = forms.TypedChoiceField(
        label="Server Verification",
        choices=BOOL_CHOICES,
        coerce=lambda x: x in (True, "True", "true"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    timestamp_verification = forms.TypedChoiceField(
        label="Timestamp Verification",
        choices=BOOL_CHOICES,
        coerce=lambda x: x in (True, "True", "true"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = UserBarcodeSettings
        fields = [
            "barcode_pull",
            "barcode",
            "server_verification",
            "timestamp_verification",
        ]
        widgets = {
            "barcode": forms.Select(attrs={"class": "form-select"}),
        }

    # Init: restrict queryset, handle “no-barcode” case, add Bootstrap styles
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Show only barcodes belonging to the current user
        queryset = Barcode.objects.filter(user=user) if user else Barcode.objects.none()
        self.fields["barcode"].queryset = queryset

        # When no barcode: force Pull=True and disable the field
        self.no_barcodes = not queryset.exists()
        if self.no_barcodes:
            self.fields["barcode_pull"].initial = True
            self.fields["barcode_pull"].disabled = True
            self.fields["barcode_pull"].required = False

        # Append Bootstrap CSS classes
        for name, field in self.fields.items():
            base_cls = (
                "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )
            field.widget.attrs["class"] = (
                f"{field.widget.attrs.get('class', '')} {base_cls}".strip()
            )

    # Form-wide validation
    def clean(self):
        cleaned = super().clean()

        # No barcode: keep Pull=True and pass validation
        if self.no_barcodes:
            cleaned["barcode_pull"] = True
            return cleaned

        pull_enabled = cleaned.get("barcode_pull")
        selected_barcode = cleaned.get("barcode")

        # Pull disabled → barcode selection is required
        if pull_enabled in (False, "False", "false"):
            if not selected_barcode:
                self.add_error(
                    "barcode", "Please select a barcode when Barcode Pull is disabled."
                )
        else:
            # Pull enabled → ignore selected barcode
            cleaned["barcode"] = None

        return cleaned
