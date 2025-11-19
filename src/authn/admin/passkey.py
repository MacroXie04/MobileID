from django.contrib import admin
from django.utils.html import format_html
from authn.models import PasskeyCredential

@admin.register(PasskeyCredential)
class PasskeyCredentialAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "credential_id_short",
        "public_key_short",
        "created_at",
        "sign_count",
    )
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "credential_id_preview",
        "public_key_preview",
        "created_at",
        "updated_at",
    )
    actions = ["replace_passkey"]

    fieldsets = (
        (None, {"fields": ("user",)}),
        (
            "Credential Info",
            {
                "fields": (
                    "credential_id_preview",
                    "public_key_preview",
                    "sign_count",
                    "attestation_format",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Credential ID")
    def credential_id_short(self, obj):
        if not obj.credential_id:
            return "—"
        return "..." + obj.credential_id[-8:]

    @admin.display(description="Public Key")
    def public_key_short(self, obj):
        if not obj.public_key:
            return "—"
        return "..." + obj.public_key[-12:]

    @admin.display(description="Credential ID (Preview)")
    def credential_id_preview(self, obj):
        if not obj.credential_id:
            return "—"
        return format_html(
            '<code style="word-break: break-all;">...{}</code>', obj.credential_id[-8:]
        )

    @admin.display(description="Public Key (Preview)")
    def public_key_preview(self, obj):
        if not obj.public_key:
            return "—"
        return format_html(
            '<code style="word-break: break-all;">...{}</code>', obj.public_key[-12:]
        )

    @admin.action(description="Replace Passkey (Delete selected)")
    def replace_passkey(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f"Successfully deleted {count} passkey(s). Users will need to register new ones.",
        )

