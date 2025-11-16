import os
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from authn.services.passkeys import (
    build_authentication_options,
    build_registration_options,
    verify_and_create_passkey,
    verify_authentication,
)
from authn.throttling import UsernameRateThrottle

from .forms import UserRegisterForm
from .helpers import (
    _b64_any_to_bytes,
    _clean_base64,
    _clear_challenge,
    _get_valid_challenge,
    _store_challenge,
)
from .serializers import EncryptedTokenObtainPairSerializer, RSAEncryptedLoginSerializer


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = EncryptedTokenObtainPairSerializer
    throttle_classes = (UsernameRateThrottle,) + tuple(api_settings.DEFAULT_THROTTLE_CLASSES)

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

            access_max_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
            refresh_max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

            response.set_cookie(
                "access_token",
                access,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=cookie_samesite,
                secure=cookie_secure,
                max_age=access_max_age,
            )

            response.set_cookie(
                "refresh_token",
                refresh,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=cookie_samesite,
                secure=cookie_secure,
                path="/authn/",
                max_age=refresh_max_age,
            )
            response.data = {"message": "Login successful"}
        return response


@api_view(["POST"])
def api_logout(request):
    # Best-effort blacklist of the refresh token (if present)
    try:
        from rest_framework_simplejwt.tokens import RefreshToken

        rt = request.COOKIES.get("refresh_token")
        if rt:
            try:
                RefreshToken(rt).blacklist()
            except Exception:
                # Blacklist may be unavailable or token invalid/expired
                pass
    except Exception:
        pass

    resp = Response({"message": "Logged out"})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token", path="/authn/")
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
    return Response({"username": request.user.username, "groups": groups, "profile": profile_data})


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

    # Base64 → bytes (robust to url-safe and missing padding)
    try:
        img_bytes = _b64_any_to_bytes(b64)
    except Exception:
        return HttpResponse(status=400)

    # Validate and detect MIME using Pillow (imghdr removed in Python 3.13)
    try:
        with Image.open(BytesIO(img_bytes)) as img:
            fmt = img.format
            mime = Image.MIME.get(fmt)
    except Exception:
        return HttpResponse(status=400)
    if not mime:
        return HttpResponse(status=400)

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
                    "errors": {field: ["This field cannot be empty"] for field in missing_fields},
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
            access_max_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
            refresh_max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

            response.set_cookie(
                "access_token",
                access_token,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=os.getenv("COOKIE_SAMESITE", "Lax"),
                secure=(os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure())
                or (os.getenv("COOKIE_SECURE", "False").lower() == "true"),
                max_age=access_max_age,
            )
            response.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=os.getenv("COOKIE_SAMESITE", "Lax"),
                secure=(os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure())
                or (os.getenv("COOKIE_SECURE", "False").lower() == "true"),
                path="/authn/",
                max_age=refresh_max_age,
            )

            return response

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

    except Exception as exc:
        return Response({"success": False, "message": f"Registration failed: {str(exc)}"}, status=500)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """
    GET: Get user profile data
    PUT: Update user profile data (name, information_id, user_profile_img_base64)
    """
    try:
        profile = request.user.userprofile
    except Exception:
        return Response({"success": False, "message": "Profile not found"}, status=404)

    if request.method == "GET":
        return Response(
            {
                "success": True,
                "data": {
                    "name": profile.name,
                    "information_id": profile.information_id,
                    "has_passkey": hasattr(request.user, "passkey"),
                },
            }
        )

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
                # Validate/normalize base64 (accept url-safe)
                img_bytes = _b64_any_to_bytes(b64)
                # Also validate it's a valid image format via Pillow
                try:
                    with Image.open(BytesIO(img_bytes)) as _:
                        pass
                except Exception:
                    raise ValueError("Not a valid image format")
                profile.user_profile_img = b64
            except Exception:
                return Response(
                    {
                        "success": False,
                        "errors": {"user_profile_img": "Invalid Base64 avatar data"},
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
    except Exception:
        return Response({"success": False, "message": "Profile not found"}, status=404)

    if "avatar" not in request.FILES:
        return Response({"success": False, "message": "No avatar file provided"}, status=400)

    avatar_file = request.FILES["avatar"]

    # Validate file type
    if not avatar_file.content_type.startswith("image/"):
        return Response({"success": False, "message": "Invalid file type"}, status=400)

    # Validate file size (5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return Response({"success": False, "message": "File size must be less than 5MB"}, status=400)

    try:
        # Process image
        form = UserRegisterForm()
        with Image.open(avatar_file) as im:
            b64 = form._pil_to_base64(im)

        # Save to profile
        profile.user_profile_img = b64
        profile.save()

        return Response({"success": True, "message": "Avatar uploaded successfully"})
    except Exception as exc:
        return Response(
            {"success": False, "message": f"Failed to process image: {str(exc)}"},
            status=500,
        )


# Passkeys / WebAuthn endpoints


@api_view(["GET"])  # Begin registration: returns PublicKeyCredentialCreationOptions
@permission_classes([IsAuthenticated])
def passkey_register_options(request):
    options = build_registration_options(request.user)
    # Store the challenge as base64url string (JSON serializable)
    _store_challenge(request, "webauthn_reg_chal", options["challenge"])
    get_token(request)
    return Response({"success": True, "publicKey": options})


@api_view(["POST"])  # Finish registration
@permission_classes([IsAuthenticated])
def passkey_register_verify(request):
    expected = _get_valid_challenge(request, "webauthn_reg_chal")
    if not expected:
        return Response({"success": False, "message": "Missing or expired challenge"}, status=400)
    try:
        verify_and_create_passkey(request.user, request.data, expected)
        _clear_challenge(request, "webauthn_reg_chal")
        return Response({"success": True})
    except Exception as exc:
        return Response({"success": False, "message": str(exc)}, status=400)


@api_view(["POST"])  # Begin authentication
@permission_classes([AllowAny])
def passkey_auth_options(request):
    # Optional username hint to narrow allowCredentials
    username = None
    try:
        username = request.data.get("username")
    except Exception:
        pass
    user = User.objects.filter(username=username).first() if username else None
    options = build_authentication_options(user)
    # Store the challenge as base64url string (JSON serializable)
    _store_challenge(request, "webauthn_auth_chal", options["challenge"])
    get_token(request)
    return Response({"success": True, "publicKey": options})


@api_view(["POST"])  # Finish authentication and set JWT cookies
@permission_classes([AllowAny])
def passkey_auth_verify(request):
    expected = _get_valid_challenge(request, "webauthn_auth_chal")
    if not expected:
        return Response({"success": False, "message": "Missing or expired challenge"}, status=400)
    try:
        user = verify_authentication(request.data, expected)
    except Exception as exc:
        return Response({"success": False, "message": str(exc)}, status=400)

    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({"success": True, "message": "Login successful"})
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "Lax")
    use_https = os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure()
    cookie_secure = True if use_https else (os.getenv("COOKIE_SECURE", "False").lower() == "true")

    access_max_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    refresh_max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

    response.set_cookie(
        "access_token",
        access_token,
        httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
        samesite=cookie_samesite,
        secure=cookie_secure,
        max_age=access_max_age,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
        samesite=cookie_samesite,
        secure=cookie_secure,
        path="/authn/",
        max_age=refresh_max_age,
    )
    _clear_challenge(request, "webauthn_auth_chal")
    return response


class RSALoginView(TokenObtainPairView):
    """
    Login view that ENFORCES RSA-encrypted password submissions.
    This is the new secure login endpoint that requires encrypted passwords with nonce.
    """

    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = RSAEncryptedLoginSerializer
    throttle_classes = (UsernameRateThrottle,) + tuple(api_settings.DEFAULT_THROTTLE_CLASSES)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access, refresh = response.data["access"], response.data["refresh"]

            # Set cookies with configurable options
            cookie_samesite = os.getenv("COOKIE_SAMESITE", "Lax")
            use_https = os.getenv("USE_HTTPS", "False").lower() == "true" or request.is_secure()
            cookie_secure = True if use_https else (os.getenv("COOKIE_SECURE", "False").lower() == "true")

            access_max_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
            refresh_max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

            response.set_cookie(
                "access_token",
                access,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=cookie_samesite,
                secure=cookie_secure,
                max_age=access_max_age,
            )

            response.set_cookie(
                "refresh_token",
                refresh,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=cookie_samesite,
                secure=cookie_secure,
                path="/authn/",
                max_age=refresh_max_age,
            )
            response.data = {"message": "Login successful"}
        return response

