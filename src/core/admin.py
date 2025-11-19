"""
Core admin configuration.
"""

from django.contrib import admin

from core.models.admin_audit import AdminAuditLog


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for AdminAuditLog model"""

    list_display = (
        "timestamp",
        "user",
        "action",
        "resource",
        "success",
        "ip_address",
    )
    list_filter = ("action", "success", "timestamp")
    search_fields = ("user__username", "resource", "ip_address")
    readonly_fields = (
        "user",
        "ip_address",
        "action",
        "resource",
        "success",
        "timestamp",
        "user_agent",
        "details",
    )
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    fieldsets = (
        (
            "Audit Information",
            {
                "fields": (
                    "timestamp",
                    "user",
                    "action",
                    "resource",
                    "success",
                )
            },
        ),
        (
            "Request Details",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                    "details",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers"""
        return request.user.is_superuser
