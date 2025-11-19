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
        "user_display",
        "action",
        "resource",
        "success",
        "ip_address",
    )
    list_select_related = ["user"]
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

    @admin.display(description="User", ordering="user__username")
    def user_display(self, obj):
        if not obj.user:
            return "-"
        try:
            return obj.user.username
        except AttributeError:
            return str(obj.user)

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers"""
        return request.user.is_superuser
