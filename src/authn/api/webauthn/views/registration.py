import logging

from authn.api.utils import set_auth_cookies
from django.contrib.auth import login
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from ..forms import UserRegisterForm


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """
    Register a new user with rudimentary rate limiting.
    """

    class RegisterThrottle(AnonRateThrottle):
        scope = "registration"

    throttle = RegisterThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {
                "success": False,
                "message": "Registration request is too frequent, please "
                "try again later",
            },
            status=429,
        )

    try:
        required_fields = [
            "username",
            "password1",
            "password2",
            "name",
            "information_id",
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
            "information_id": request.data.get("information_id"),
            "user_profile_img_base64": request.data.get("user_profile_img_base64", ""),
        }

        form = UserRegisterForm(data=form_data)

        if form.is_valid():
            user = form.save()
            login(request, user)

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
