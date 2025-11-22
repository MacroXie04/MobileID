from django.contrib import admin
from django.utils.html import format_html
from authn.models import RSAKeyPair


@admin.register(RSAKeyPair)
class RSAKeyPairAdmin(admin.ModelAdmin):
    list_display = (
        "kid_short",
        "key_size",
        "is_active",
        "created_at",
        "rotated_at",
    )
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
                '<code style="word-break: break-all;">{}<br/>...<br/>{}' "</code>",
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
                '<code style="word-break: break-all; color: #d32f2f;">{}<br/>'
                "...<br/>{}</code>",
                key[:50],
                key[-50:],
            )
        return format_html(
            '<code style="word-break: break-all; color: #d32f2f;">{}</code>',
            key,
        )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active keys
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)
