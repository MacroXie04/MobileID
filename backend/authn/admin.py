from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django import forms
from django.utils.html import format_html
import json
import textwrap

from authn.models import (
    UserProfile,
    UserExtendedData,
    QuickAction,
    UserChangeLog,
)

# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────
def _pretty_json(value: dict, *, max_len: int = 120) -> str:
    """Return a compact, truncated JSON representation for list_display."""
    pretty = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return textwrap.shorten(pretty, width=max_len, placeholder="…")


# ──────────────────────────────────────────────────────────────
#  User Admin Customization (Group Filter + is_staff sync)
# ──────────────────────────────────────────────────────────────
class LimitedGroupUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_groups = ["User", "School", "Staff"]
        self.fields["groups"].queryset = Group.objects.filter(name__in=allowed_groups)


class LimitedGroupUserAdmin(UserAdmin):
    form = LimitedGroupUserChangeForm
    filter_horizontal = ("groups",)  # nice multiselect

    def save_model(self, request, obj, form, change):
        # Keep is_staff in sync with "Staff" group
        super().save_model(request, obj, form, change)
        staff_group = Group.objects.filter(name="Staff").first()
        if staff_group:
            obj.is_staff = staff_group in obj.groups.all()
            obj.save(update_fields=["is_staff"])


# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, LimitedGroupUserAdmin)


# ──────────────────────────────────────────────────────────────
#  Authn Admin Models
# ──────────────────────────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "information_id", "avatar", "profile_uuid")
    search_fields = ("user__username", "name", "information_id")
    readonly_fields = ("profile_uuid", "avatar")
    list_select_related = ("user",)

    @admin.display(description="Avatar", ordering=False)
    def avatar(self, obj):
        if not obj.user_profile_img:
            return "—"
        return format_html(
            '<img src="data:image/png;base64,{}" width="48" height="48" style="object-fit:cover;border-radius:4px;" />',
            obj.user_profile_img,
        )


@admin.register(UserExtendedData)
class UserExtendedDataAdmin(admin.ModelAdmin):
    list_display = ("user", "preview")
    search_fields = ("user__username",)
    readonly_fields = ("preview_full",)
    list_select_related = ("user",)

    @admin.display(description="Extended Data (brief)", ordering=False)
    def preview(self, obj):
        return _pretty_json(obj.extended_data)

    @admin.display(description="Extended Data (full)", ordering=False)
    def preview_full(self, obj):
        return format_html(
            "<pre style='white-space:pre-wrap'>{}</pre>",
            json.dumps(obj.extended_data, indent=2, ensure_ascii=False),
        )


@admin.register(QuickAction)
class QuickActionAdmin(admin.ModelAdmin):
    list_display = ("action_name", "short_description", "json_patch_preview")
    search_fields = ("action_name",)
    readonly_fields = ("json_patch_preview",)

    @admin.display(description="Description")
    def short_description(self, obj):
        return textwrap.shorten(obj.action_description, width=60, placeholder="…")

    @admin.display(description="JSON Patch (brief)")
    def json_patch_preview(self, obj):
        return _pretty_json(obj.json_patch)


@admin.register(UserChangeLog)
class UserChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "staff_user",
        "target_user",
        "short_change_description",
    )
    list_filter = ("staff_user", "target_user")
    search_fields = ("staff_user__username", "target_user__username", "change_description")
    readonly_fields = ("timestamp", "data_before_pretty", "data_after_pretty")
    date_hierarchy = "timestamp"
    list_per_page = 25

    @admin.display(description="Change Description")
    def short_change_description(self, obj):
        return textwrap.shorten(obj.change_description, width=80, placeholder="…")

    @admin.display(description="Data Before")
    def data_before_pretty(self, obj):
        return format_html(
            "<pre style='white-space:pre-wrap'>{}</pre>",
            json.dumps(obj.data_before, indent=2, ensure_ascii=False),
        )

    @admin.display(description="Data After")
    def data_after_pretty(self, obj):
        return format_html(
            "<pre style='white-space:pre-wrap'>{}</pre>",
            json.dumps(obj.data_after, indent=2, ensure_ascii=False),
        )

class LimitedGroupUserAdmin(UserAdmin):
    form = LimitedGroupUserChangeForm
    filter_horizontal = ("groups",)

    # List only username + group info
    list_display = ("username", "display_groups", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        staff_group = Group.objects.filter(name="Staff").first()
        if staff_group:
            obj.is_staff = staff_group in obj.groups.all()
            obj.save(update_fields=["is_staff"])

    @admin.display(description="Groups")
    def display_groups(self, obj):
        return ", ".join(group.name for group in obj.groups.all()) or "—"

# Unregister default and register customized version
admin.site.unregister(User)
admin.site.register(User, LimitedGroupUserAdmin)

