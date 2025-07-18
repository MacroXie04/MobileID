from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed

from barcode.settings import (ACCOUNT_LOCKOUT_DURATION,
                              MAX_FAILED_LOGIN_ATTEMPTS)
from mobileid.models import UserProfile
from mobileid.throttling import LoginRateThrottle


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that handles disabled accounts.
    Allows disabled users to authenticate but returns a specific error for disabled accounts.
    """
    
    def validate(self, attrs):
        # First, try to authenticate normally
        try:
            data = super().validate(attrs)
            return data
        except Exception as e:
            error_str = str(e)
            if "No active account found" in error_str:
                username = attrs.get('username')
                try:
                    user = User.objects.get(username=username)
                    if not user.is_active:
                        raise AuthenticationFailed("Account is disabled. Please contact administrator.")
                    else:
                        raise e
                except User.DoesNotExist:
                    raise AuthenticationFailed("Invalid credentials.")
            else:
                raise e


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for token generation with rate limiting.
    Extends the standard TokenObtainPairView but adds throttling to prevent brute force attacks.
    Also tracks failed login attempts and locks accounts after too many failed attempts.
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        # Check if the username exists and if the account is locked
        username = request.data.get("username", "")
        try:
            user = User.objects.get(username=username)
            user_profile, created = UserProfile.objects.get_or_create(user=user)

            # Check if account is locked
            if user_profile.is_locked:
                if (
                    user_profile.locked_until
                    and user_profile.locked_until > timezone.now()
                ):
                    # Account is still locked
                    minutes_remaining = int(
                        (user_profile.locked_until - timezone.now()).total_seconds()
                        / 60
                    )
                    return Response(
                        {
                            "detail": f"Account is locked due to too many failed login attempts. Try again in {minutes_remaining} minutes.",
                            "failed_attempts": user_profile.failed_login_attempts,
                            "is_locked": True,
                            "locked_until": user_profile.locked_until,
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                else:
                    # Lock period has expired, unlock the account
                    user_profile.is_locked = False
                    user_profile.locked_until = None
                    user_profile.save(update_fields=["is_locked", "locked_until"])
        except User.DoesNotExist:
            pass

        serializer = self.get_serializer(data=request.data)

        try:
            if serializer.is_valid():
                if "user" in locals():
                    user_profile.failed_login_attempts = 0
                    user_profile.save(update_fields=["failed_login_attempts"])
                return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except AuthenticationFailed as e:
            error_detail = str(e)
            if "Account is disabled" in error_detail:
                return Response(
                    {
                        "detail": error_detail,
                        "account_disabled": True,
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                return Response({"detail": error_detail}, status=status.HTTP_401_UNAUTHORIZED)

        # Authentication failed, increment failed attempts
        if "user" in locals():
            user_profile.failed_login_attempts += 1

            if user_profile.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user_profile.is_locked = True
                user_profile.locked_until = timezone.now() + timedelta(
                    minutes=ACCOUNT_LOCKOUT_DURATION
                )
                user_profile.save(
                    update_fields=[
                        "failed_login_attempts",
                        "is_locked",
                        "locked_until",
                    ]
                )

                return Response(
                    {
                        "detail": f"Account is locked due to too many failed login attempts. Try again in {ACCOUNT_LOCKOUT_DURATION} minutes.",
                        "failed_attempts": user_profile.failed_login_attempts,
                        "is_locked": True,
                        "locked_until": user_profile.locked_until,
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                user_profile.save(update_fields=["failed_login_attempts"])

                response_data = serializer.errors
                response_data["failed_attempts"] = (
                    user_profile.failed_login_attempts
                )
                response_data["max_attempts"] = MAX_FAILED_LOGIN_ATTEMPTS
                response_data["attempts_remaining"] = (
                    MAX_FAILED_LOGIN_ATTEMPTS - user_profile.failed_login_attempts
                )

                return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
