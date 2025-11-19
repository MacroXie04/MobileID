from django.contrib import admin
from django.utils.html import format_html

from ..models import BarcodeUsage, BarcodeUserProfile


class BarcodeUsageInline(admin.TabularInline):
    """Inline admin for BarcodeUsage to display within Barcode admin"""

    model = BarcodeUsage
    extra = 0
    readonly_fields = ("total_usage", "last_used")
    can_delete = False
    show_change_link = True


class BarcodeUserProfileInline(admin.TabularInline):
    """Inline admin for BarcodeUserProfile linked to a Barcode"""

    model = BarcodeUserProfile
    fk_name = "linked_barcode"
    extra = 0
    readonly_fields = ("avatar_preview",)
    can_delete = True
    show_change_link = True
    fields = (
        "name",
        "information_id",
        "gender_barcode",
        "user_profile_img",
        "avatar_preview",
    )

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if obj and getattr(obj, "user_profile_img", None):
            return format_html(
                '<img src="data:image/png;base64,{}" style="height:64px;width:64px;border-radius:8px;object-fit:cover;" />',
                obj.user_profile_img,
            )
        return "-"

    def has_add_permission(self, request, obj=None):
        return False
