import logging

from django.conf import settings
from django.contrib.auth import login
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from authn.api.utils import set_auth_cookies
from authn.services.webauthn import generate_unique_information_id
from authn.throttling import RegisterRateThrottle

from ..forms import UserRegisterForm


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def api_register(request):
    """
    Register a new user with rate limiting via RegisterRateThrottle.
    """

    try:
        required_fields = [
            "username",
            "password1",
            "password2",
            "name",
        ]
        missing_fields = [
            field for field in required_fields if not request.data.get(field)
        ]

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

        form_data = {
            "username": request.data.get("username"),
            "password1": request.data.get("password1"),
            "password2": request.data.get("password2"),
            "name": request.data.get("name"),
            "information_id": generate_unique_information_id(),
            "user_profile_img_base64": request.data.get("user_profile_img_base64", ""),
        }

        form = UserRegisterForm(data=form_data)

        if form.is_valid():
            user = form.save()
            login(request, user)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response_data = {
                "success": True,
                "message": "Registration successful",
                "data": {
                    "username": user.username,
                    "groups": list(user.groups.values_list("name", flat=True)),
                },
            }
            if settings.AUTH_EXPOSE_TOKENS_IN_BODY:
                response_data["access"] = access_token
                response_data["refresh"] = refresh_token
            response = Response(response_data)
            set_auth_cookies(response, access_token, refresh_token, request=request)

            return response

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

    except Exception:
        logging.exception("Error occurred during user registration")
        return Response(
            {
                "success": False,
                "message": "Registration failed due to an internal error.",
            },
            status=500,
        )
