from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from index.models import Barcode, UserBarcodePullSettings, UserBarcodeSettings, Transaction
from index.services.usage_limit import UsageLimitService

from .constants import (
    BARCODE_DYNAMIC,
    BARCODE_IDENTIFICATION,
    BARCODE_OTHERS,
    RESULT_TEMPLATE,
)
from .identification import _create_identification_barcode
from .usage import _touch_barcode_usage
from .utils import _timestamp


def generate_barcode(user) -> dict:
    """Generate or refresh a barcode for *user* based on their group membership."""
    result = RESULT_TEMPLATE.copy()

    # Determine account type via groups
    is_staff = user.groups.filter(name="Staff").exists()
    is_user = user.groups.filter(name="User").exists()
    is_school = user.groups.filter(name="School").exists()

    # STAFF — not allowed
    if is_staff:
        result.update(
            status="error", message="Staff accounts cannot generate barcodes."
        )
        return result

    # Unknown or missing group
    if not (is_user or is_school):
        result.update(status="error", message="Permission Denied.")
        return result

    # --------------------------------------------------------------
    # handle generate barcode

    # Wrap DB operations in an explicit transaction for select_for_update
    with transaction.atomic():
        (
            settings,
            _,
        ) = UserBarcodeSettings.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "barcode": None,
                "associate_user_profile_with_barcode": False,
            },
        )

        # handle barcode pull settings
        (
            pull_settings,
            _,
        ) = UserBarcodePullSettings.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "pull_setting": "Disable",
                "gender_setting": "Unknow",
            },
        )

        if (
            pull_settings.pull_setting == "Enable"
            and user.groups.filter(name="School").exists()
        ):
            # 1. Check for recent personal usage (Stickiness) - 10 min
            cutoff_10m = timezone.now() - timedelta(minutes=10)
            recent_txn = (
                Transaction.objects.filter(user=user, time_created__gte=cutoff_10m)
                .order_by("-time_created")
                .first()
            )

            candidate = None
            if recent_txn and recent_txn.barcode_used:
                candidate = recent_txn.barcode_used

            # 2. Pull from pool if no candidate
            if not candidate:
                cutoff_5m = timezone.now() - timedelta(minutes=5)

                # Base query: User's own barcodes OR Shareable Dynamic barcodes
                qs = Barcode.objects.filter(
                    Q(user=user)
                    | Q(share_with_others=True, barcode_type=BARCODE_DYNAMIC)
                )

                # Gender filter
                qs = qs.filter(
                    barcodeuserprofile__gender_barcode=pull_settings.gender_setting  # noqa: E501
                )

                # Usage filter: Exclude if used by ANYONE in last 5 mins
                qs = qs.exclude(barcodeusage__last_used__gte=cutoff_5m)

                # Pick one (randomly)
                if qs.exists():
                    candidate = qs.order_by("?").first()

            # 3. Apply selection
            if candidate:
                settings.barcode = candidate
                settings.save()

        # Use the user-selected barcode
        selected = settings.barcode

        # For User type, ensure they have an identification barcode
        if is_user:
            # Find or create their identification barcode
            ident_barcode = Barcode.objects.filter(
                user=user, barcode_type=BARCODE_IDENTIFICATION
            ).first()

            if not ident_barcode:
                # Create one if it doesn't exist
                ident_barcode = _create_identification_barcode(user)

            # Force the selection to identification barcode
            selected = ident_barcode
            settings.barcode = ident_barcode
            settings.associate_user_profile_with_barcode = False
            settings.save()

        if not selected:
            result.update(status="error", message="No barcode selected.")
            return result

        # Permission check:
        # - Users can always use their own barcodes
        # - For barcodes owned by others:
        #   * Only DynamicBarcode is eligible, and only if share_with_others=True  # noqa: E501
        if selected.user != user:
            if selected.barcode_type != BARCODE_DYNAMIC:
                result.update(status="error", message="Permission Denied.")
                return result
            if not getattr(selected, "share_with_others", False):
                result.update(status="error", message="Permission Denied.")
                return result

        # Handle by barcode type
        if selected.barcode_type == BARCODE_IDENTIFICATION:
            # Create fresh identification barcode
            new_bc = _create_identification_barcode(user)
            settings.barcode = new_bc
            settings.save(update_fields=["barcode"])

            # Check usage limits for the new barcode
            allowed, limit_error = UsageLimitService.check_all_limits(new_bc)
            if not allowed:
                result.update(status="error", message=limit_error)
                return result

            # Track usage for identification barcodes
            _touch_barcode_usage(new_bc, request_user=user)

            result.update(
                status="success",
                message="Identification barcode",
                barcode_type=BARCODE_IDENTIFICATION,
                barcode=new_bc.barcode,
            )
            return result

        if selected.barcode_type == BARCODE_DYNAMIC:
            # Check usage limits before generating
            allowed, limit_error = UsageLimitService.check_all_limits(selected)
            if not allowed:
                result.update(status="error", message=limit_error)
                return result

            # Update usage stats
            _touch_barcode_usage(selected, request_user=user)

            full = f"{_timestamp()}{selected.barcode}"
            result.update(
                status="success",
                message=f"Dynamic: {selected.barcode[-4:]}",
                barcode_type=BARCODE_DYNAMIC,
                barcode=full,
            )
            return result

        if selected.barcode_type == BARCODE_OTHERS:
            # Check usage limits before generating
            allowed, limit_error = UsageLimitService.check_all_limits(selected)
            if not allowed:
                result.update(status="error", message=limit_error)
                return result

            # Track usage for other barcode types
            _touch_barcode_usage(selected, request_user=user)

            result.update(
                status="success",
                message=f"Barcode ending with {selected.barcode[-4:]}",
                barcode_type=BARCODE_OTHERS,
                barcode=selected.barcode,
            )
            return result

        # Fallback error
        result.update(status="error", message="Invalid barcode type.")
        return result
