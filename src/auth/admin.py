from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.html import format_html
import json
import textwrap
import uuid

from src.authn.models import (
    UserProfile,
    Passkey,
)
from mobileid.models import UserBarcodeSettings, Barcode


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
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=True,
        label="Group",
        help_text="Select the user's group (only one allowed)",
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default groups field
        if "groups" in self.fields:
            del self.fields["groups"]

        # Set up the single group field
        allowed_groups = ["User", "School", "Staff"]
        self.fields["group"].queryset = Group.objects.filter(name__in=allowed_groups)

        # Set initial value if user already has a group
        if self.instance and self.instance.pk:
            user_group = self.instance.groups.first()
            if user_group:
                self.fields["group"].initial = user_group

    def save(self, commit=True):
        # Just save the user, let the admin handle group assignment
        user = super().save(commit=commit)
        return user


class LimitedGroupUserAddForm(UserCreationForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=True,
        label="Group",
        help_text="Select the user's group (only one allowed)",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password1",
            "password2",
            "first_name",
            "last_name",
            "email",
            "group",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_groups = ["User", "School", "Staff"]
        self.fields["group"].queryset = Group.objects.filter(name__in=allowed_groups)

    def save(self, commit=True):
        # Just save the user, let the admin handle group assignment
        user = super().save(commit=commit)
        return user


class LimitedGroupUserAdmin(UserAdmin):
    form = LimitedGroupUserChangeForm
    add_form = LimitedGroupUserAddForm
    # Remove filter_horizontal since we're using a single choice field

    # Custom fieldsets that exclude 'groups' and include our 'group' field
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Group Assignment", {"fields": ("group",)}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "user_permissions"),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Fieldsets for adding a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Group Assignment", {"fields": ("group",)}),
    )

    # List only username + group info
    list_display = (
        "username",
        "display_group",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")

    def save_model(self, request, obj, form, change):
        # Save the model first
        super().save_model(request, obj, form, change)

        # Store old groups for later comparison
        if change and hasattr(self, "_old_groups"):
            self._old_groups_for_user = self._old_groups

    def save_related(self, request, form, formsets, change):
        # Handle formsets first
        for formset in formsets:
            self.save_formset(request, form, formset, change=change)

        # Get the user instance
        user = form.instance

        # Handle group assignment from our custom field
        if hasattr(form, "cleaned_data") and "group" in form.cleaned_data:
            selected_group = form.cleaned_data.get("group")

            # Clear all groups and set only the selected one
            user.groups.clear()
            if selected_group:
                user.groups.add(selected_group)

        # Handle user_permissions (from the default Django admin)
        if hasattr(form, "cleaned_data") and "user_permissions" in form.cleaned_data:
            user.user_permissions.set(form.cleaned_data["user_permissions"])

        # Now handle additional logic after groups have been saved
        staff_group = Group.objects.filter(name="Staff").first()

        # Keep is_staff in sync with "Staff" group
        if staff_group:
            user.is_staff = staff_group in user.groups.all()
            user.save(update_fields=["is_staff"])

        # Check if user moved from Staff to User or School
        old_groups = getattr(self, "_old_groups_for_user", set())
        new_groups = set(user.groups.all())

        if change and staff_group in old_groups and staff_group not in new_groups:
            user_group = Group.objects.filter(name="User").first()
            school_group = Group.objects.filter(name="School").first()

            # If the user is now in User or School group
            if (user_group in new_groups) or (school_group in new_groups):
                # Create UserProfile if it doesn't exist
                if not hasattr(user, "userprofile"):
                    UserProfile.objects.create(
                        user=user,
                        name=f"{user.first_name} {user.last_name}".strip()
                        or user.username,
                        information_id=user.username,  # Default to username, can be updated later
                        user_profile_img="",  # Empty profile image
                    )

                # Create UserBarcodeSettings if it doesn't exist
                try:
                    UserBarcodeSettings.objects.get(user=user)
                except UserBarcodeSettings.DoesNotExist:
                    UserBarcodeSettings.objects.create(
                        user=user,
                        barcode=None,
                        server_verification=False,
                        barcode_pull=False,  # Default to False for new users
                    )

                # Create an identification barcode for the user if it doesn't exist
                if not Barcode.objects.filter(
                    user=user, barcode_type="Identification"
                ).exists():
                    # Generate a unique identification barcode
                    barcode_value = f"{user.username}_{uuid.uuid4().hex[:8]}"
                    Barcode.objects.create(
                        user=user, barcode=barcode_value, barcode_type="Identification"
                    )

    def get_form(self, request, obj=None, **kwargs):
        # Store old groups before form is processed
        if obj:
            self._old_groups = set(obj.groups.all())
        return super().get_form(request, obj, **kwargs)

    @admin.display(description="Group")
    def display_group(self, obj):
        group = obj.groups.first()
        return group.name if group else "—"


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


@admin.register(Passkey)
class PasskeyAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "credential_id", "public_key", "created_at")
    search_fields = ("user__username", "name", "credential_id")
    readonly_fields = ("created_at",)
    list_select_related = ("user",)

    def name(self, obj):
        return obj.user.username
