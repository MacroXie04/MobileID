import json
import textwrap
import uuid

from authn.models import UserProfile, RSAKeyPair
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from index.models import UserBarcodeSettings, Barcode
from index.services.transactions import TransactionService


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
                        associate_user_profile_with_barcode=False,  # Default to False for new users
                    )

                # Create an identification barcode for the user if it doesn't exist
                if not Barcode.objects.filter(
                        user=user, barcode_type="Identification"
                ).exists():
                    # Generate a unique identification barcode
                    barcode_value = f"{user.username}_{uuid.uuid4().hex[:8]}"
                    ident_barcode = Barcode.objects.create(
                        user=user, barcode=barcode_value, barcode_type="Identification"
                    )
                    # Record transaction for identification barcode creation
                    TransactionService.create_transaction(
                        user=user,
                        barcode=ident_barcode,
                    )

        # Check if user changed from School to User group
        if change:
            school_group = Group.objects.filter(name="School").first()
            user_group = Group.objects.filter(name="User").first()

            # If changed from School to User
            if (
                    school_group in old_groups
                    and school_group not in new_groups
                    and user_group in new_groups
            ):
                # Update UserBarcodeSettings to use identification barcode
                try:
                    settings = UserBarcodeSettings.objects.get(user=user)
                    # Find the user's identification barcode
                    ident_barcode = Barcode.objects.filter(
                        user=user, barcode_type="Identification"
                    ).first()

                    if ident_barcode:
                        settings.barcode = ident_barcode
                        settings.associate_user_profile_with_barcode = (
                            False  # Force this to False for User type
                        )
                        settings.save()
                except UserBarcodeSettings.DoesNotExist:
                    # Create settings with identification barcode
                    ident_barcode = Barcode.objects.filter(
                        user=user, barcode_type="Identification"
                    ).first()

                    if ident_barcode:
                        UserBarcodeSettings.objects.create(
                            user=user,
                            barcode=ident_barcode,
                            server_verification=False,
                            associate_user_profile_with_barcode=False,
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
    list_display = (
        "user",
        "name",
        "information_id",
        "avatar_preview",
        "profile_uuid_short",
    )
    search_fields = ("user__username", "name", "information_id", "profile_uuid")
    readonly_fields = ("profile_uuid", "avatar_display")
    list_select_related = ("user",)
    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Profile Details", {"fields": ("name", "information_id", "profile_uuid")}),
        ("Avatar", {"fields": ("user_profile_img", "avatar_display")}),
    )

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if not obj.user_profile_img:
            return "—"
        return format_html(
            '<img src="data:image/png;base64,{}" width="48" height="48" style="object-fit:cover;border-radius:4px;" />',
            obj.user_profile_img,
        )

    @admin.display(description="Current Avatar")
    def avatar_display(self, obj):
        if not obj.user_profile_img:
            return "Not set"
        return format_html(
            '<img src="data:image/png;base64,{}" width="128" height="128" style="object-fit:cover;border-radius:4px;" />',
            obj.user_profile_img,
        )

    @admin.display(description="UUID")
    def profile_uuid_short(self, obj):
        return str(obj.profile_uuid)[:8] + "…"


@admin.register(RSAKeyPair)
class RSAKeyPairAdmin(admin.ModelAdmin):
    list_display = ("kid_short", "key_size", "is_active", "created_at", "rotated_at")
    list_filter = ("is_active", "key_size", "created_at")
    readonly_fields = (
        "kid",
        "created_at",
        "updated_at",
        "rotated_at",
        "public_key_preview",
        "private_key_preview",
    )
    search_fields = ("kid",)
    fieldsets = (
        (None, {"fields": ("kid", "key_size", "is_active")}),
        ("Public Key", {"fields": ("public_key", "public_key_preview")}),
        ("Private Key", {"fields": ("private_key", "private_key_preview")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "rotated_at")}),
    )

    @admin.display(description="Key ID")
    def kid_short(self, obj):
        return str(obj.kid)[:8] + "…"

    @admin.display(description="Public Key Preview")
    def public_key_preview(self, obj):
        if not obj.public_key:
            return "—"
        # Show first and last 50 chars
        key = obj.public_key.strip()
        if len(key) > 100:
            return format_html(
                '<code style="word-break: break-all;">{}<br/>...<br/>{}</code>',
                key[:50],
                key[-50:],
            )
        return format_html('<code style="word-break: break-all;">{}</code>', key)

    @admin.display(description="Private Key Preview")
    def private_key_preview(self, obj):
        if not obj.private_key:
            return "—"
        # Show first and last 50 chars only (security)
        key = obj.private_key.strip()
        if len(key) > 100:
            return format_html(
                '<code style="word-break: break-all; color: #d32f2f;">{}<br/>...<br/>{}</code>',
                key[:50],
                key[-50:],
            )
        return format_html(
            '<code style="word-break: break-all; color: #d32f2f;">{}</code>', key
        )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active keys
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)
