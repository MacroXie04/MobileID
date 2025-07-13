from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone

# import forms
from mobileid.forms.WebAuthnForms import UserLoginForm, UserRegisterForm
from mobileid.models import UserProfile


def web_register(request):
    if request.method == "POST":
        # Bind both form fields and uploaded files
        form = UserRegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            return redirect("mobileid:web_login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, "webauthn/register.html", {"form": form})


def web_login(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            # Check if user exists
            try:
                user_obj = User.objects.get(username=username)

                # Get or create user profile
                user_profile, created = UserProfile.objects.get_or_create(user=user_obj)

                # Check if account is locked
                if user_profile.is_locked:
                    # Check if lockout period has expired
                    if (
                        user_profile.locked_until
                        and user_profile.locked_until < timezone.now()
                    ):
                        # Unlock the account
                        user_profile.is_locked = False
                        user_profile.failed_login_attempts = 0
                        user_profile.locked_until = None
                        user_profile.save()
                    else:
                        # Account is still locked
                        remaining_time = (
                            int(
                                (
                                    user_profile.locked_until - timezone.now()
                                ).total_seconds()
                                / 60
                            )
                            + 1
                        )
                        form.add_error(
                            None,
                            f"Account is locked. Please try again after {remaining_time} minutes.",
                        )
                        return render(request, "webauthn/login.html", {"form": form})

                # Attempt authentication
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    # Check if user is active
                    if not user.is_active:
                        form.add_error(None, "Your account is currently disabled.")
                        return render(request, "webauthn/login.html", {"form": form})

                    # Reset failed login attempts on successful login
                    user_profile.failed_login_attempts = 0
                    user_profile.save()

                    login(request, user)
                    return redirect("mobileid:web_index")
                else:
                    # Increment failed login attempts
                    user_profile.failed_login_attempts += 1

                    # Check if account should be locked
                    if (
                        user_profile.failed_login_attempts
                        >= settings.MAX_FAILED_LOGIN_ATTEMPTS
                    ):
                        user_profile.is_locked = True
                        user_profile.locked_until = timezone.now() + timezone.timedelta(
                            minutes=settings.ACCOUNT_LOCKOUT_DURATION
                        )
                        form.add_error(
                            None,
                            f"Too many failed login attempts. Your account has been locked for {settings.ACCOUNT_LOCKOUT_DURATION} minutes.",
                        )
                    else:
                        remaining_attempts = (
                            settings.MAX_FAILED_LOGIN_ATTEMPTS
                            - user_profile.failed_login_attempts
                        )
                        form.add_error(
                            None,
                            f"Invalid username or password. {remaining_attempts} attempts remaining before account is locked.",
                        )

                    user_profile.save()
            except User.DoesNotExist:
                # User doesn't exist, but don't reveal this information
                form.add_error(None, "Invalid username or password")

    else:
        form = UserLoginForm()

    return render(request, "webauthn/login.html", {"form": form})


@login_required(login_url="login")
def web_logout(request):
    logout(request)
    return redirect("mobileid:web_login")
