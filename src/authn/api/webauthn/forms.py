import base64
from io import BytesIO

from PIL import Image
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from authn.services import (
    create_user_profile,
    generate_unique_information_id,
)

from .helpers import _clean_base64


class UserRegisterForm(forms.Form):
    username = User._meta.get_field("username").formfield()
    password1 = forms.CharField(label="Password", strip=False)
    password2 = forms.CharField(label="Confirm Password", strip=False)
    name = forms.CharField(max_length=100, label="Name")
    information_id = forms.CharField(
        max_length=100, label="Information ID", required=False
    )

    # original file (hidden input, file selection is handled by JS)
    user_profile_img = forms.ImageField(required=False, label="")

    # Cropper.js generated Base64 (hidden field)
    user_profile_img_base64 = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="",
        validators=[MaxLengthValidator(30_000)],
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

    def clean_username(self):
        username = User.normalize_username(self.cleaned_data["username"])
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("A user with that username already exists."))
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error(
                "password2",
                ValidationError(_("Passwords do not match"), code="password_mismatch"),
            )

        if password1:
            candidate_user = User(username=cleaned_data.get("username") or "")
            try:
                validate_password(password1, user=candidate_user)
            except ValidationError as exc:
                self.add_error("password1", exc)

        return cleaned_data

    # save
    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("UserRegisterForm must be validated before saving.")

        user = User(username=self.cleaned_data["username"])
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False

        if commit:
            user.save()

        name = self.cleaned_data["name"]
        info_id = (
            self.cleaned_data.get("information_id") or generate_unique_information_id()
        )

        # check if there is a pre-cropped Base64
        avatar_b64 = self.cleaned_data.get("user_profile_img_base64", "")

        # if not, use the uploaded original file for cropping
        if not avatar_b64 and self.cleaned_data.get("user_profile_img"):
            with Image.open(self.cleaned_data["user_profile_img"]) as im:
                avatar_b64 = self._pil_to_base64(im)

        # if still empty, store None → database field is NULL
        avatar_b64_or_none = avatar_b64 or None

        if commit:
            create_user_profile(user, name, info_id, avatar_b64_or_none)

        return user
