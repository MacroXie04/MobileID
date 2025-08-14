# authn/views.py
import base64
import imghdr
import os
from binascii import Error as BinasciiError
from io import BytesIO

from PIL import Image
from authn.services.webauthn import create_user_profile
from django import forms
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView


def _clean_base64(b64: str) -> str:
    """
    Remove any data-URI prefix and return the raw Base64.
    """
    if b64.startswith("data:image"):
        b64 = b64.split(",", 1)[1]
    return b64.strip()


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


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access, refresh = response.data["access"], response.data["refresh"]

            # Set cookies with configurable options
            # For HTTPS development, use Lax instead of None
            cookie_samesite = os.getenv("COOKIE_SAMESITE", "Lax")
            # Determine HTTPS by env USE_HTTPS or request.is_secure()
            use_https = os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure()
            cookie_secure = True if use_https else (os.getenv("COOKIE_SECURE", "False").lower() == "true")

            response.set_cookie(
                "access_token",
                access,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=cookie_samesite,
                secure=cookie_secure,
                max_age=int(os.getenv("ACCESS_TOKEN_AGE", 1800)),
            )

            response.set_cookie(
                "refresh_token",
                refresh,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=cookie_samesite,
                secure=cookie_secure,
                max_age=int(os.getenv("REFRESH_TOKEN_AGE", 604800)),
            )
            response.data = {"message": "Login successful"}
        return response


@api_view(["POST"])
def api_logout(request):
    resp = Response({"message": "Logged out"})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    groups = list(request.user.groups.values_list("name", flat=True))
    try:
        profile = request.user.userprofile
        profile_data = {
            "name": profile.name,
            "information_id": profile.information_id,
        }
    except Exception:
        profile_data = None
    return Response(
        {"username": request.user.username, "groups": groups, "profile": profile_data}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_img(request):
    """
    Stream the current user's avatar (image/* response).

    • `UserProfile.user_profile_img` only saves *pure* Base64 strings
      (if it still contains a data-URI prefix, it can be automatically removed).
    • return the correct MIME type; if Base64 is invalid → 400
    • user/avatar does not exist → 404
    """
    profile = getattr(request.user, "userprofile", None)
    if not profile or not profile.user_profile_img:
        return HttpResponse(status=404)

    b64 = profile.user_profile_img
    if b64.startswith("data:image"):
        b64 = b64.split(",", 1)[1]

    # Base64 → bytes
    try:
        img_bytes = base64.b64decode(b64, validate=True)
    except (BinasciiError, ValueError):
        return HttpResponse(status=400)

    # guess image format (png / jpeg / gif / webp …)
    ext = imghdr.what(None, h=img_bytes) or "png"
    mime = f"image/{'jpeg' if ext == 'jpg' else ext}"

    response = HttpResponse(img_bytes, content_type=mime)
    response["Cache-Control"] = "private, max-age=3600"  # 1 hour
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """
    register a new user
    """

    # apply registration rate limit
    class RegisterThrottle(AnonRateThrottle):
        scope = "registration"

    # manually check rate limit
    throttle = RegisterThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {
                "success": False,
                "message": "Registration request is too frequent, please try again later",
            },
            status=429,
        )

    try:
        # validate required fields
        required_fields = [
            "username",
            "password1",
            "password2",
            "name",
            "information_id",
        ]
        missing_fields = []
        for field in required_fields:
            if not request.data.get(field):
                missing_fields.append(field)

        if missing_fields:
            return Response(
                {
                    "success": False,
                    "message": "Missing required fields",
                    "errors": {
                        field: ["This field cannot be empty"]
                        for field in missing_fields
                    },
                },
                status=400,
            )

        # prepare form data
        form_data = {
            "username": request.data.get("username"),
            "password1": request.data.get("password1"),
            "password2": request.data.get("password2"),
            "name": request.data.get("name"),
            "information_id": request.data.get("information_id"),
            "user_profile_img_base64": request.data.get("user_profile_img_base64", ""),
        }

        # create form instance for validation
        form = UserRegisterForm(data=form_data)

        if form.is_valid():
            # save user
            user = form.save()

            # login user
            login(request, user)

            # set JWT cookies
            from rest_framework_simplejwt.tokens import RefreshToken

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response(
                {
                    "success": True,
                    "message": "Registration successful",
                    "data": {
                        "username": user.username,
                        "groups": list(user.groups.values_list("name", flat=True)),
                    },
                }
            )

            # set JWT cookies
            response.set_cookie(
                "access_token",
                access_token,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=os.getenv("COOKIE_SAMESITE", "Lax"),
                secure=(os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure()) or (
                            os.getenv("COOKIE_SECURE", "False").lower() == "true"),
                max_age=int(os.getenv("ACCESS_TOKEN_AGE", 1800)),
            )
            response.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=os.getenv("COOKIE_SAMESITE", "Lax"),
                secure=(os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure()) or (
                            os.getenv("COOKIE_SECURE", "False").lower() == "true"),
                max_age=int(os.getenv("REFRESH_TOKEN_AGE", 604800)),
            )

            return response

        else:
            # form validation failed, return error message
            errors = {}
            for field, field_errors in form.errors.items():
                if field == "__all__":
                    errors["general"] = field_errors
                else:
                    errors[field] = field_errors

            return Response(
                {
                    "success": False,
                    "message": "Registration information validation failed",
                    "errors": errors,
                },
                status=400,
            )

    except Exception as e:
        return Response(
            {"success": False, "message": f"Registration failed: {str(e)}"}, status=500
        )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """
    GET: Get user profile data
    PUT: Update user profile data (name, information_id, user_profile_img_base64)
    """
    try:
        profile = request.user.userprofile
    except:
        return Response({"success": False, "message": "Profile not found"}, status=404)

    if request.method == "GET":
        return Response(
            {
                "success": True,
                "data": {
                    "name": profile.name,
                    "information_id": profile.information_id,
                },
            }
        )

    elif request.method == "PUT":
        # Update profile fields
        data = request.data

        # Validate fields
        errors = {}
        if "name" in data and not data["name"].strip():
            errors["name"] = "Name cannot be empty"
        if "information_id" in data and not data["information_id"].strip():
            errors["information_id"] = "Information ID cannot be empty"

        if errors:
            return Response({"success": False, "errors": errors}, status=400)

        # Update fields
        if "name" in data:
            profile.name = data["name"]
        if "information_id" in data:
            profile.information_id = data["information_id"]
        if "user_profile_img_base64" in data:
            # Clean base64
            b64 = _clean_base64(data["user_profile_img_base64"])
            if b64:
                try:
                    # Validate base64
                    base64.b64decode(b64, validate=True)
                    profile.user_profile_img = b64
                except Exception:
                    return Response(
                        {
                            "success": False,
                            "errors": {
                                "user_profile_img": "Invalid Base64 avatar data"
                            },
                        },
                        status=400,
                    )
            else:
                # Empty string means remove avatar
                profile.user_profile_img = None

        profile.save()

        return Response({"success": True, "message": "Profile updated successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_avatar_upload(request):
    """
    Upload avatar as multipart form data
    This endpoint is kept for compatibility but converts to base64
    """
    try:
        profile = request.user.userprofile
    except:
        return Response({"success": False, "message": "Profile not found"}, status=404)

    if "avatar" not in request.FILES:
        return Response(
            {"success": False, "message": "No avatar file provided"}, status=400
        )

    avatar_file = request.FILES["avatar"]

    # Validate file type
    if not avatar_file.content_type.startswith("image/"):
        return Response({"success": False, "message": "Invalid file type"}, status=400)

    # Validate file size (5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return Response(
            {"success": False, "message": "File size must be less than 5MB"}, status=400
        )

    try:
        # Process image
        form = UserRegisterForm()
        with Image.open(avatar_file) as im:
            b64 = form._pil_to_base64(im)

        # Save to profile
        profile.user_profile_img = b64
        profile.save()

        return Response({"success": True, "message": "Avatar uploaded successfully"})
    except Exception as e:
        return Response(
            {"success": False, "message": f"Failed to process image: {str(e)}"},
            status=500,
        )
