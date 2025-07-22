import base64
from io import BytesIO

from PIL import Image
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from authn.services.webauthn import create_user_profile


# UserLoginForm
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your username"}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter your password"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if self.errors.get(field_name):
                field.widget.attrs["class"] += " is-invalid"


class UserRegisterForm(UserCreationForm):
    # Extra visible fields
    name = forms.CharField(max_length=100, label="Name")
    information_id = forms.CharField(max_length=100, label="Information ID")

    # Raw file input (hidden by CSS – selection handled via JS)
    user_profile_img = forms.ImageField(required=False, label="")

    # Base64 string produced by Cropper.js
    user_profile_img_base64 = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="",
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

    # ---------- validation helpers ---------- #
    def clean(self):
        data = super().clean()
        # Avatar is optional - no validation required
        return data

    @staticmethod
    def _pil_to_base64(pil_img: Image.Image) -> str:
        """Center-crop, resize → 128×128 PNG → Base64 (no data URI)."""
        min_side = min(pil_img.size)
        left = (pil_img.width - min_side) // 2
        top = (pil_img.height - min_side) // 2
        pil_img = pil_img.crop((left, top, left + min_side, top + min_side))
        pil_img = pil_img.resize((128, 128), Image.LANCZOS)

        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # ---------- persistence ---------- #
    def save(self, commit=True):
        user = super().save(commit)
        name = self.cleaned_data["name"]
        info_id = self.cleaned_data["information_id"]

        # Determine avatar data - prefer client-cropped Base64, else process raw file, else use default
        avatar_b64 = ""
        if self.cleaned_data.get("user_profile_img_base64"):
            avatar_b64 = self.cleaned_data["user_profile_img_base64"]
        elif self.cleaned_data.get("user_profile_img"):
            with Image.open(self.cleaned_data["user_profile_img"]) as im:
                avatar_b64 = self._pil_to_base64(im)
        # If no avatar provided, avatar_b64 remains empty string

        create_user_profile(user, name, info_id, avatar_b64)
        return user
