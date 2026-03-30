from rest_framework import status
from rest_framework.response import Response

from index.models import Barcode, BarcodeUsage, UserBarcodeSettings
from index.serializers import BarcodeSerializer, BarcodeCreateSerializer
from index.services.transactions import TransactionService


class DashboardBarcodeCRUDMixin:
    """PUT/PATCH/DELETE handlers: barcode create, update, and delete."""

    def put(self, request):
        """Create new barcode"""
        serializer = BarcodeCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            # Record a transaction for barcode creation via service layer
            TransactionService.create_transaction(user=request.user, barcode=barcode)
            return Response(
                {
                    "status": "success",
                    "message": "New barcode added successfully",
                    "barcode": BarcodeSerializer(
                        barcode, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request):
        """Update properties of a barcode owned by the current user (share flag and daily limit)"""  # noqa: E501
        barcode_id = request.data.get("barcode_id")
        share_with_others = request.data.get("share_with_others")
        daily_usage_limit = request.data.get("daily_usage_limit")

        if not barcode_id:
            return Response(
                {"status": "error", "message": "barcode_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            barcode = Barcode.objects.get(pk=barcode_id, user=request.user)
        except Barcode.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Barcode not found or you do not have "
                    "permission to update it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Identification barcodes cannot be updated
        if barcode.barcode_type == "Identification":
            return Response(
                {
                    "status": "error",
                    "message": "Identification barcodes cannot be modified",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update share_with_others if provided
        if share_with_others is not None:
            # Coerce to boolean if sent as string
            if isinstance(share_with_others, str):
                share_with_others = share_with_others.lower() in [
                    "1",
                    "true",
                    "yes",
                    "on",
                ]
            barcode.share_with_others = bool(share_with_others)
            barcode.save()

        # Update daily_usage_limit if provided
        if daily_usage_limit is not None:
            try:
                # Ensure it's a non-negative integer
                limit_value = int(daily_usage_limit)
                if limit_value < 0:
                    return Response(
                        {
                            "status": "error",
                            "message": "Daily usage limit must be 0 or " "greater",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Get or create BarcodeUsage record
                usage, _ = BarcodeUsage.objects.get_or_create(
                    barcode=barcode, defaults={"total_usage": 0}
                )
                usage.daily_usage_limit = limit_value
                usage.save()
            except (ValueError, TypeError):
                return Response(
                    {
                        "status": "error",
                        "message": "Daily usage limit must be a valid number",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "status": "success",
                "message": "Barcode updated successfully",
                "barcode": BarcodeSerializer(
                    barcode, context={"request": request}
                ).data,
            }
        )

    def delete(self, request):
        """
        Delete barcode - users may delete only their own barcodes
        (DynamicBarcode and Others types)
        """
        barcode_id = request.data.get("barcode_id")

        if not barcode_id:
            return Response(
                {"status": "error", "message": "Barcode ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # All users can only delete barcodes they own
        try:
            barcode = Barcode.objects.get(
                pk=barcode_id,
                user=request.user,
                barcode_type__in=["DynamicBarcode", "Others"],
            )
        except Barcode.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Barcode not found or you do not have "
                    "permission to delete it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if this barcode is currently selected in settings
        settings = UserBarcodeSettings.objects.filter(
            user=request.user, barcode=barcode
        ).first()

        if settings:
            settings.barcode = None
            settings.save()

        barcode.delete()

        return Response(
            {"status": "success", "message": "Barcode deleted successfully"}
        )
