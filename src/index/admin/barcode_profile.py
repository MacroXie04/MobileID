from django.contrib import admin
from django.utils.html import format_html

from ..models import BarcodeUserProfile


@admin.register(BarcodeUserProfile)
class BarcodeUserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for BarcodeUserProfile model"""

    list_display = (
        "linked_barcode_display",
        "name",
        "information_id",
        "gender_barcode",
        "avatar_preview",
    )
    list_filter = ("gender_barcode",)
    search_fields = (
        "name",
        "information_id",
        "linked_barcode__barcode",
        "linked_barcode__user__username",
    )
    readonly_fields = ("avatar_preview",)
    ordering = ("name",)
    list_per_page = 50
    save_on_top = True

    fieldsets = (
        (
            "Profile",
            {"fields": ("linked_barcode", "name", "information_id", "gender_barcode")},
        ),
        (
            "Avatar (PNG base64 128x128)",
            {"fields": ("user_profile_img", "avatar_preview")},
        ),
    )

    @admin.display(description="Linked Barcode")
    def linked_barcode_display(self, obj):
        try:
            return f"...{obj.linked_barcode.barcode[-4:]} ({obj.linked_barcode.barcode_type})"
        except Exception:
            return "-"

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if obj.user_profile_img:
            return format_html(
                '<img src="data:image/png;base64,{}" style="height:64px;width:64px;border-radius:8px;object-fit:cover;" />',
                obj.user_profile_img,
            )
        return "-"
