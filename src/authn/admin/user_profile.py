from django.contrib import admin
from django.utils.html import format_html
from authn.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "information_id",
        "avatar_preview",
        "profile_uuid_short",
    )
    search_fields = (
        "user__username",
        "name",
        "information_id",
        "profile_uuid",
    )
    readonly_fields = ("profile_uuid", "avatar_display")
    list_select_related = ("user",)
    fieldsets = (
        (None, {"fields": ("user",)}),
        (
            "Profile Details",
            {"fields": ("name", "information_id", "profile_uuid")},
        ),
        ("Avatar", {"fields": ("user_profile_img", "avatar_display")}),
    )

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if not obj.user_profile_img:
            return "—"
        return format_html(
            '<img src="data:image/png;base64,{}" width="48" height="48" '
            'style="object-fit:cover;border-radius:4px;" />',
            obj.user_profile_img,
        )

    @admin.display(description="Current Avatar")
    def avatar_display(self, obj):
        if not obj.user_profile_img:
            return "Not set"
        return format_html(
            '<img src="data:image/png;base64,{}" width="128" height="128" '
            'style="object-fit:cover;border-radius:4px;" />',
            obj.user_profile_img,
        )

    @admin.display(description="UUID")
    def profile_uuid_short(self, obj):
        return str(obj.profile_uuid)[:8] + "…"
