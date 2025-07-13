import base64
from io import BytesIO

from PIL import Image
from django import forms

from mobileid.models import (
    UserProfile,
    UserBarcodeSettings,
    Barcode,
)


class StudentInformationUpdateForm(forms.ModelForm):
    # Avatar is optional on update – keep existing one if nothing uploaded
    user_profile_img = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    class Meta:
        model = UserProfile
        fields = ["name", "information_id", "user_profile_img"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Full name"}
            ),
            "information_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Student ID"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure Bootstrap styling & error feedback
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = (
                field.widget.attrs.get("class", "") + " form-control"
            )
            if self.errors.get(field_name):
                field.widget.attrs["class"] += " is-invalid"

    def save(self, commit=True):
        instance = super().save(commit=False)

        img_file = self.cleaned_data.get("user_profile_img")

        if not img_file or isinstance(img_file, str):
            if commit:
                instance.save()
            return instance

        with Image.open(img_file) as im:
            min_side = min(im.size)
            left = (im.width - min_side) // 2
            top = (im.height - min_side) // 2
            im = im.crop((left, top, left + min_side, top + min_side))
            im = im.resize((128, 128), Image.LANCZOS)

            buffer = BytesIO()
            im.save(buffer, format="PNG")
            instance.user_profile_img = base64.b64encode(buffer.getvalue()).decode(
                "utf-8"
            )

        if commit:
            instance.save()
        return instance


import base64
from io import BytesIO

from PIL import Image
from django import forms

from mobileid.models import (
    UserProfile,
    UserBarcodeSettings,
    Barcode,
)


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
