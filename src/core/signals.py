"""
Signal handlers for core app.

Connects to Django admin login/logout signals to log admin access.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from core.middleware.admin_audit import log_admin_login, log_admin_logout


@receiver(user_logged_in)
def log_admin_login_signal(sender, request, user, **kwargs):
    """
    Log admin login when user logs in through admin interface.
    """
    # Only log if user is staff
    if user.is_staff:
        # Check if request path indicates admin login
        if request and hasattr(request, "path"):
            from django.conf import settings
            admin_path = f"/{settings.ADMIN_URL_PATH}/"
            if request.path.startswith(admin_path):
                log_admin_login(request, user, success=True)


@receiver(user_logged_out)
def log_admin_logout_signal(sender, request, user, **kwargs):
    """
    Log admin logout when user logs out through admin interface.
    """
    # Only log if user is staff
    if user and user.is_staff:
        if request and hasattr(request, "path"):
            from django.conf import settings
            admin_path = f"/{settings.ADMIN_URL_PATH}/"
            if request.path.startswith(admin_path):
                log_admin_logout(request, user)

