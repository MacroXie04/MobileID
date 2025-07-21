import base64
from io import BytesIO

from PIL import Image
from django import forms
from django.core.files.uploadedfile import UploadedFile

from authn.models import UserProfile

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

        img_file = self.cleaned_data.get("user_profile_img")
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
