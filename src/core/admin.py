"""
Core admin configuration.
"""

from django.contrib import admin

from core.models import AdminAuditLog, AdminOneTimePass


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


@admin.register(AdminOneTimePass)
class AdminOneTimePassAdmin(admin.ModelAdmin):
    """Admin configuration for AdminOneTimePass model"""

    list_display = (
        "user",
        "pass_code_display",
        "created_at",
        "expires_at",
        "is_used",
        "is_valid_display",
    )
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ["user"]
    list_select_related = ("user",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("user", "pass_code")}),
        (
            "Status",
            {
                "fields": (
                    "is_used",
                    "created_at",
                    "expires_at",
                )
            },
        ),
    )

    @admin.display(description="Valid", boolean=True)
    def is_valid_display(self, obj):
        return obj.is_valid()

    @admin.display(description="Pass Code")
    def pass_code_display(self, obj):
        return "********"  # Mask password in list view for security

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
