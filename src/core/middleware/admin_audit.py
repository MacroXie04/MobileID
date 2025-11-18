"""
Admin audit logging middleware.

Logs all admin access and actions for security auditing.
"""

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.db import transaction

from core.models.admin_audit import AdminAuditLog


class AdminAuditMiddleware:
    """
    Middleware that logs admin access and actions.

    Records login/logout events and tracks admin page access.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL_PATH}/"

    def __call__(self, request):
        # Only process admin requests
        if not request.path.startswith(self.admin_path):
            return self.get_response(request)

        # Log admin access
        if request.user.is_authenticated and request.user.is_staff:
            self._log_admin_access(request)

        response = self.get_response(request)

        # Log logout if it happened
        if request.path.endswith("/logout/") and request.user.is_authenticated:
            self._log_admin_action(request, AdminAuditLog.LOGOUT, success=True)

        return response

    def _log_admin_access(self, request):
        """
        Log admin page access.

        Only logs significant actions, not every page view to avoid log spam.
        """
        # Skip logging for static files and common admin assets
        if any(
            request.path.endswith(ext)
            for ext in [".css", ".js", ".png", ".jpg", ".gif", ".ico", ".svg"]
        ):
            return

        # Skip logging for GET requests to avoid log spam
        # Only log POST requests (form submissions, actions)
        if request.method != "POST":
            return

        # Determine action type based on path
        resource = self._extract_resource(request.path)
        
        # Determine action from path patterns
        if "/add/" in request.path:
            action = AdminAuditLog.ADD
        elif "/change/" in request.path or "/changelist/" in request.path:
            action = AdminAuditLog.CHANGE
        elif "/delete/" in request.path:
            action = AdminAuditLog.DELETE
        else:
            # For other POST requests, log as action
            action = AdminAuditLog.ACTION

        # Log the action
        self._log_admin_action(request, action, resource=resource, success=True)

    def _log_admin_action(
        self, request, action, resource="", success=True, details=None
    ):
        """
        Create an admin audit log entry.
        """
        if not request.user.is_authenticated:
            return

        try:
            with transaction.atomic():
                AdminAuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=self._get_client_ip(request),
                    action=action,
                    resource=resource,
                    success=success,
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                    details=details or {},
                )
        except Exception:
            # Don't let audit logging break the request
            pass

    def _extract_resource(self, path):
        """
        Extract resource name from admin path.

        Examples:
        /admin/auth/user/ -> "auth.user"
        /admin/auth/user/1/change/ -> "auth.user"
        """
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            # Format: /admin/app/model/...
            return f"{parts[1]}.{parts[2]}"
        return ""

    def _get_client_ip(self, request):
        """
        Extract client IP from request, handling proxy headers.
        """
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


def log_admin_login(request, user, success=True):
    """
    Helper function to log admin login attempts.

    Can be called from admin login view or signal handlers.
    """
    try:
        AdminAuditLog.objects.create(
            user=user if success else None,
            ip_address=_get_client_ip_from_request(request),
            action=AdminAuditLog.LOGIN,
            resource="admin",
            success=success,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            details={"username": getattr(user, "username", "") if user else ""},
        )
    except Exception:
        pass


def log_admin_logout(request, user):
    """
    Helper function to log admin logout events.
    """
    try:
        AdminAuditLog.objects.create(
            user=user,
            ip_address=_get_client_ip_from_request(request),
            action=AdminAuditLog.LOGOUT,
            resource="admin",
            success=True,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
    except Exception:
        pass


def _get_client_ip_from_request(request):
    """Extract client IP from request."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")

