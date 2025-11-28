from django.contrib import admin

from ..models import UserBarcodeSettings, UserBarcodePullSettings


@admin.register(UserBarcodeSettings)
class UserBarcodeSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for UserBarcodeSettings model"""

    list_display = (
        "user",
        "barcode",
        "associate_user_profile_with_barcode",
        "scanner_detection_enabled",
        "prefer_front_camera",
    )
    list_filter = (
        "associate_user_profile_with_barcode",
        "scanner_detection_enabled",
        "prefer_front_camera",
    )
    search_fields = ("user__username", "barcode__barcode")
    ordering = ("user__username",)
    autocomplete_fields = ["user", "barcode"]
    list_per_page = 50
    list_select_related = ("user", "barcode")
    show_full_result_count = False
    save_on_top = True

    fieldsets = (
        (None, {"fields": ("user",)}),
        (
            "Barcode Settings",
            {
                "fields": (
                    "barcode",
                    "associate_user_profile_with_barcode",
                )
            },
        ),
        (
            "Camera Settings",
            {
                "fields": (
                    "scanner_detection_enabled",
                    "prefer_front_camera",
                )
            },
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("user", "barcode")


@admin.register(UserBarcodePullSettings)
class UserBarcodePullSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for UserBarcodePullSettings model"""

    list_display = ("user", "pull_setting", "gender_setting")
    list_filter = ("pull_setting", "gender_setting")
    search_fields = ("user__username", "user__email")
    ordering = ("user__username",)
    autocomplete_fields = ["user"]
    list_per_page = 50
    list_select_related = ("user",)
    show_full_result_count = False
    save_on_top = True

    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Pull Settings", {"fields": ("pull_setting", "gender_setting")}),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("user")
