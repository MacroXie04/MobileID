import base64
from io import BytesIO

from PIL import Image
from authn.services.webauthn import create_user_profile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

from .helpers import _clean_base64


class UserRegisterForm(UserCreationForm):
    # extra fields
    name = forms.CharField(max_length=100, label="Name")
    information_id = forms.CharField(max_length=100, label="Information ID")

    # original file (hidden input, file selection is handled by JS)
    user_profile_img = forms.ImageField(required=False, label="")

    # Cropper.js generated Base64 (hidden field)
    user_profile_img_base64 = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="",
        validators=[MaxLengthValidator(30_000)],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password1",
            "password2",
            "name",
            "information_id",
            "user_profile_img",
            "user_profile_img_base64",
        )

    # helpers
    @staticmethod
    def _pil_to_base64(pil_img: Image.Image) -> str:
        """
        Center-crop → resize 128*128 → PNG → Base64 (utf-8 str, no prefix).
        """
        min_side = min(pil_img.size)
        left = (pil_img.width - min_side) // 2
        top = (pil_img.height - min_side) // 2
        pil_img = pil_img.crop((left, top, left + min_side, top + min_side))
        pil_img = pil_img.resize((128, 128), Image.LANCZOS)

        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # validation
    def clean_user_profile_img_base64(self):
        """
        • remove data-URI prefix
        • ensure content is valid Base64
        """
        b64 = _clean_base64(self.cleaned_data.get("user_profile_img_base64", ""))
        if not b64:
            return ""

        try:
            # b64decode(validate=True) checks validity
            base64.b64decode(b64, validate=True)
        except Exception:
            raise ValidationError("Invalid Base64 avatar data.")

        return b64

    # save
    def save(self, commit=True):
        user = super().save(commit)
        name = self.cleaned_data["name"]
        info_id = self.cleaned_data["information_id"]

        # check if there is a pre-cropped Base64
        avatar_b64 = self.cleaned_data.get("user_profile_img_base64", "")

        # if not, use the uploaded original file for cropping
        if not avatar_b64 and self.cleaned_data.get("user_profile_img"):
            with Image.open(self.cleaned_data["user_profile_img"]) as im:
                avatar_b64 = self._pil_to_base64(im)

        # if still empty, store None → database field is NULL
        avatar_b64_or_none = avatar_b64 or None

        create_user_profile(user, name, info_id, avatar_b64_or_none)
        return user
